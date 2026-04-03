from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sys
from sqlalchemy import inspect, text
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# Add parent directory to path so we can import API module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database
from database import db
from models import User, Task, EmotionLog, UserActivityLog
from modules.emotion import preload_deepface_model

# Resolve frontend directory and serve it from Flask so one server can host API + UI
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root, "Frontend")
load_dotenv(os.path.join(project_root, ".env"))

# Initialize Flask app
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# Database Configuration (PostgreSQL is used in production to ensure persistent storage across deployments)

db_url = os.environ.get("DATABASE_URL")
if db_url:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    print("Using DB:", db_url)
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///local.db"
    print("Using DB: sqlite:///local.db")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.secret_key = app.config['SECRET_KEY']
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_EXPIRES_SECONDS', '3600'))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_EXPIRES_SECONDS', str(30 * 24 * 3600)))
app.config['PROPAGATE_EXCEPTIONS'] = False
is_production = os.environ.get("RENDER") or os.environ.get("ENV") == "production"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None" if is_production else "Lax",
    SESSION_COOKIE_SECURE=True if is_production else False,
)
session_lifetime_seconds = int(os.getenv('SESSION_LIFETIME_SECONDS', str(7 * 24 * 3600)))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=session_lifetime_seconds)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Initialize Database with app
db.init_app(app)
jwt = JWTManager(app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)
limiter.init_app(app)

# Preload DeepFace emotion model to avoid first-request latency or missing weights.
try:
    preload_deepface_model()
except Exception as exc:
    print(f"[deepface] preload failed: {exc}")

# Optional server-side sessions (e.g., Render + Redis)
try:
    from flask_session import Session  # type: ignore
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        app.config["SESSION_TYPE"] = "redis"
        try:
            from redis import Redis  # type: ignore
            app.config["SESSION_REDIS"] = Redis.from_url(redis_url)
        except Exception as redis_exc:
            print(f"[session] Redis unavailable, falling back to filesystem: {redis_exc}")
            app.config["SESSION_TYPE"] = "filesystem"
            app.config["SESSION_FILE_DIR"] = os.path.join(project_root, ".flask_sessions")
    else:
        app.config["SESSION_TYPE"] = "filesystem"
        app.config["SESSION_FILE_DIR"] = os.path.join(project_root, ".flask_sessions")
    if app.config.get("SESSION_TYPE") == "filesystem":
        os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    Session(app)
except Exception as exc:
    print(f"[session] Flask-Session not enabled: {exc}")

# Enable CORS for frontend communication
default_origins = ["http://localhost:5000", "http://localhost:3000"]
env_origins_raw = os.getenv("CORS_ORIGINS", "")
env_origins = [o.strip() for o in env_origins_raw.split(",") if o.strip()]
allowed_origins = list(dict.fromkeys(env_origins + default_origins))
vercel_origin_regex = r"^https://.*\.vercel\.app$"
CORS(app, origins=allowed_origins + [vercel_origin_regex], supports_credentials=True)

# Import and register routes
from API.routes import auth_bp
from task_routes import task_bp
from log_routes import logs_bp

app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)
app.register_blueprint(logs_bp)


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({"error": "Invalid token"}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({"error": "Authorization token required"}), 401


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded"}), 429


@app.errorhandler(Exception)
def generic_error_handler(e):
    if isinstance(e, HTTPException):
        return jsonify({"error": e.description}), e.code
    # Hide internals in API responses
    print(f"[ERROR] {type(e).__name__}: {e}")
    return jsonify({"error": "Internal server error"}), 500


@app.route('/')
def home():
    return app.send_static_file("index.html")


@app.route("/debug/users", methods=["GET"])
def debug_users():
    debug_key = os.getenv("DEBUG_KEY", "secret123")
    if request.headers.get("x-debug-key") != debug_key:
        return jsonify({"error": "Unauthorized"}), 403
    users = User.query.order_by(User.id.asc()).all()
    payload = [user.to_dict() for user in users]
    return jsonify({"count": len(payload), "users": payload}), 200


def dispatch_all_due_reminders():
    """Daily reminder sweep for all users with pending due reminders."""
    from notifications import (
        send_email,
        send_sms,
        build_reminder_content,
        build_sms_reminder_content,
        build_empty_nudge_content,
        build_empty_nudge_sms,
        PHONE_REGEX,
    )

    with app.app_context():
        now = datetime.utcnow()
        cooldown_minutes = int(os.getenv("REMINDER_COOLDOWN_MINUTES", "30"))
        max_per_user_per_run = int(os.getenv("REMINDER_MAX_PER_USER_PER_RUN", "5"))
        users = User.query.all()
        for user in users:
            tasks = Task.query.filter_by(user_id=user.email).all()
            due = [t for t in tasks if t.reminder_at and not t.reminder_sent and t.reminder_at <= now and not t.completed]

            sent_for_user = 0
            if due:
                for task in due:
                    if sent_for_user >= max_per_user_per_run:
                        break
                    if task.reminder_last_sent_at and now - task.reminder_last_sent_at < timedelta(minutes=cooldown_minutes):
                        continue

                    method = (task.reminder_method or user.notification_preference or "email").lower()

                    ok_email = False
                    ok_sms = False
                    phone = task.reminder_phone or user.phone
                    email_attemptable = bool(user.email) if method in ["email", "both"] else False
                    sms_attemptable = bool(phone and PHONE_REGEX.match(phone)) if method in ["sms", "both"] else False

                    if method in ["email", "both"] and email_attemptable:
                        subject, body = build_reminder_content(
                            task.title,
                            user.email,
                            importance=task.importance,
                            urgency=task.urgency,
                            is_daily=True,
                        )
                        ok_email = send_email(user.email, subject, body, owner_email=user.email)
                    if method in ["sms", "both"] and sms_attemptable:
                        ok_sms = send_sms(
                            phone,
                            build_sms_reminder_content(
                                task.title,
                                importance=task.importance,
                                urgency=task.urgency,
                                is_daily=True,
                            ),
                        )

                    delivery_satisfied = (
                        (method == "email" and ok_email)
                        or (method == "sms" and ok_sms)
                        or (method == "both" and (ok_email or ok_sms))
                    )
                    terminal_misconfig = (
                        (method == "email" and not email_attemptable)
                        or (method == "sms" and not sms_attemptable)
                        or (method == "both" and not email_attemptable and not sms_attemptable)
                    )
                    if delivery_satisfied or terminal_misconfig:
                        task.reminder_sent = True
                        task.reminder_last_sent_at = now
                        sent_for_user += 1

            # Daily "no tasks" gentle reminder if user has no active tasks.
            active_tasks = [t for t in tasks if not t.completed]
            if not active_tasks:
                last_nudge = user.last_empty_nudge_at
                if not last_nudge or last_nudge.date() != now.date():
                    method = (user.notification_preference or "email").lower()
                    to_email = user.email
                    phone = user.phone
                    email_attemptable = bool(to_email) if method in ["email", "both"] else False
                    sms_attemptable = bool(phone and PHONE_REGEX.match(phone)) if method in ["sms", "both"] else False

                    ok_email = False
                    ok_sms = False
                    if method in ["email", "both"] and email_attemptable:
                        subject, body = build_empty_nudge_content(user.email, is_daily=True)
                        ok_email = send_email(to_email, subject, body, owner_email=user.email)
                    if method in ["sms", "both"] and sms_attemptable:
                        sms_body = build_empty_nudge_sms(user.email, is_daily=True)
                        ok_sms = send_sms(phone, sms_body)

                    terminal_misconfig = (
                        (method == "email" and not email_attemptable)
                        or (method == "sms" and not sms_attemptable)
                        or (method == "both" and not email_attemptable and not sms_attemptable)
                    )
                    if ok_email or ok_sms or terminal_misconfig:
                        user.last_empty_nudge_at = now

        db.session.commit()

# Create database tables on startup
with app.app_context():
    try:
        db.create_all()
        print("✅ DB connected")
    except Exception as e:
        print("❌ DB error:", e)
    inspector = inspect(db.engine)
    bool_default = "FALSE" if db.engine.dialect.name == "postgresql" else "0"
    if 'users' in inspector.get_table_names():
        user_columns = {c['name'] for c in inspector.get_columns('users')}
        user_alters = []
        datetime_type = "TIMESTAMP" if db.engine.dialect.name == "postgresql" else "DATETIME"
        if 'full_name' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN full_name VARCHAR(200)")
        if 'phone' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN phone VARCHAR(30)")
        if 'notification_preference' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN notification_preference VARCHAR(20) DEFAULT 'email'")
        if 'gmail_connected' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN gmail_connected BOOLEAN DEFAULT 0")
        if 'gmail_email' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN gmail_email VARCHAR(120)")
        if 'gmail_access_token' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN gmail_access_token TEXT")
        if 'gmail_refresh_token' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN gmail_refresh_token TEXT")
        if 'gmail_token_expiry' not in user_columns:
            user_alters.append(f"ALTER TABLE users ADD COLUMN gmail_token_expiry {datetime_type}")
        if 'gmail_scope' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN gmail_scope TEXT")
        if 'last_empty_nudge_at' not in user_columns:
            user_alters.append(f"ALTER TABLE users ADD COLUMN last_empty_nudge_at {datetime_type}")
        if 'last_welcome_sent_at' not in user_columns:
            user_alters.append(f"ALTER TABLE users ADD COLUMN last_welcome_sent_at {datetime_type}")
        for stmt in user_alters:
            db.session.execute(text(stmt))
        if user_alters:
            db.session.commit()

    if 'tasks' in inspector.get_table_names():
        columns = {c['name'] for c in inspector.get_columns('tasks')}
        alters = []
        datetime_type = "TIMESTAMP" if db.engine.dialect.name == "postgresql" else "DATETIME"
        if 'due_at' not in columns:
            alters.append(f"ALTER TABLE tasks ADD COLUMN due_at {datetime_type}")
        if 'due_time' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN due_time TIME")
        if 'reminder_at' not in columns:
            alters.append(f"ALTER TABLE tasks ADD COLUMN reminder_at {datetime_type}")
        if 'reminder_method' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_method VARCHAR(20)")
        if 'reminder_sent' not in columns:
            alters.append(f"ALTER TABLE tasks ADD COLUMN reminder_sent BOOLEAN DEFAULT {bool_default}")
        if 'reminder_last_sent_at' not in columns:
            alters.append(f"ALTER TABLE tasks ADD COLUMN reminder_last_sent_at {datetime_type}")
        if 'reminder_phone' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_phone VARCHAR(30)")
        for stmt in alters:
            db.session.execute(text(stmt))
        if alters:
            db.session.commit()

    if 'user_activity_logs' in inspector.get_table_names():
        log_columns = {c['name'] for c in inspector.get_columns('user_activity_logs')}
        log_alters = []
        datetime_type = "TIMESTAMP" if db.engine.dialect.name == "postgresql" else "DATETIME"
        if 'user_email' not in log_columns:
            log_alters.append("ALTER TABLE user_activity_logs ADD COLUMN user_email VARCHAR(120)")
        if 'action' not in log_columns:
            log_alters.append("ALTER TABLE user_activity_logs ADD COLUMN action VARCHAR(120)")
        if 'details' not in log_columns:
            log_alters.append("ALTER TABLE user_activity_logs ADD COLUMN details TEXT")
        if 'timestamp' not in log_columns:
            log_alters.append(f"ALTER TABLE user_activity_logs ADD COLUMN timestamp {datetime_type}")
        for stmt in log_alters:
            db.session.execute(text(stmt))
        if log_alters:
            db.session.commit()
    print("Database initialized successfully!")

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    dispatch_all_due_reminders,
    trigger="cron",
    hour=int(os.getenv("REMINDER_DAILY_HOUR_UTC", "8")),
    minute=0,
    id="daily-reminder-sweep",
    replace_existing=True,
)
scheduler.start()

if __name__ == "__main__":
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
