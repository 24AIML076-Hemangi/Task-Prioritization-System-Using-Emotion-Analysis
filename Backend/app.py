from flask import Flask, redirect, jsonify
from flask_cors import CORS
import os
import sys
import sqlite3
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

# Resolve frontend directory and serve it from Flask so one server can host API + UI
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root, "Frontend")
load_dotenv(os.path.join(project_root, ".env"))

# Initialize Flask app
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')

# SQLite Database Configuration
# Database Configuration (Render + Local Support)
basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix for Render postgres:// issue
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    print("✅ Using Render PostgreSQL")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "tasks.db")}'
    print("⚠️ Using Local SQLite")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-change-me')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.getenv('JWT_ACCESS_EXPIRES_SECONDS', '3600'))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.getenv('JWT_REFRESH_EXPIRES_SECONDS', str(30 * 24 * 3600)))
app.config['PROPAGATE_EXCEPTIONS'] = False

# Initialize Database with app
db.init_app(app)
jwt = JWTManager(app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
)
limiter.init_app(app)

# Enable CORS for frontend communication
allowed_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5000").split(",") if o.strip()]
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

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
    return redirect('/login.html')


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

def _is_postgres_url(url):
    if not url:
        return False
    return url.startswith("postgresql://") or url.startswith("postgresql+psycopg2://")

def _sqlite_row_value(row, key, default=None):
    keys = row.keys()
    return row[key] if key in keys else default


def sync_sqlite_to_postgres_if_enabled():
    """Copy SQLite data into PostgreSQL with idempotent upserts."""
    if not _is_postgres_url(app.config['SQLALCHEMY_DATABASE_URI']):
        return

    if os.getenv("SQLITE_MIGRATE_ON_STARTUP", "1") != "1":
        return

    sqlite_path = os.getenv("SQLITE_SOURCE_DB", os.path.join(basedir, "tasks.db"))
    if not os.path.exists(sqlite_path):
        print(f"[MIGRATION] SQLite source not found: {sqlite_path}")
        return

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cur = sqlite_conn.cursor()
    table_names = {
        r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }

    migrated_counts = {"users": 0, "tasks": 0, "emotion_logs": 0}
    with db.engine.begin() as conn:
        if "users" in table_names:
            users = cur.execute("SELECT * FROM users").fetchall()
            for row in users:
                conn.execute(
                    text(
                        """
                        INSERT INTO users (id, username, email, password_hash, phone, notification_preference, created_at, updated_at)
                        VALUES (:id, :username, :email, :password_hash, :phone, :notification_preference, :created_at, :updated_at)
                        ON CONFLICT (email) DO UPDATE SET
                            username = EXCLUDED.username,
                            password_hash = EXCLUDED.password_hash,
                            phone = EXCLUDED.phone,
                            notification_preference = EXCLUDED.notification_preference,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    {
                        "id": row["id"],
                        "username": _sqlite_row_value(row, "username"),
                        "email": row["email"],
                        "password_hash": row["password_hash"],
                        "phone": _sqlite_row_value(row, "phone"),
                        "notification_preference": _sqlite_row_value(row, "notification_preference", "email"),
                        "created_at": _sqlite_row_value(row, "created_at"),
                        "updated_at": _sqlite_row_value(row, "updated_at"),
                    },
                )
            migrated_counts["users"] = len(users)

        if "tasks" in table_names:
            tasks = cur.execute("SELECT * FROM tasks").fetchall()
            for row in tasks:
                conn.execute(
                    text(
                        """
                        INSERT INTO tasks (
                            id, user_id, title, importance, urgency, completed, emotion_applied,
                            due_time,
                            due_at, reminder_at, reminder_method, reminder_sent, reminder_last_sent_at, reminder_phone,
                            created_at, updated_at
                        )
                        VALUES (
                            :id, :user_id, :title, :importance, :urgency, :completed, :emotion_applied,
                            :due_time,
                            :due_at, :reminder_at, :reminder_method, :reminder_sent, :reminder_last_sent_at, :reminder_phone,
                            :created_at, :updated_at
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            title = EXCLUDED.title,
                            importance = EXCLUDED.importance,
                            urgency = EXCLUDED.urgency,
                            completed = EXCLUDED.completed,
                            emotion_applied = EXCLUDED.emotion_applied,
                            due_time = EXCLUDED.due_time,
                            due_at = EXCLUDED.due_at,
                            reminder_at = EXCLUDED.reminder_at,
                            reminder_method = EXCLUDED.reminder_method,
                            reminder_sent = EXCLUDED.reminder_sent,
                            reminder_last_sent_at = EXCLUDED.reminder_last_sent_at,
                            reminder_phone = EXCLUDED.reminder_phone,
                            updated_at = EXCLUDED.updated_at
                        """
                    ),
                    {
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "title": row["title"],
                        "importance": _sqlite_row_value(row, "importance", "not-important"),
                        "urgency": _sqlite_row_value(row, "urgency", "not-urgent"),
                        "completed": bool(_sqlite_row_value(row, "completed", 0)),
                        "emotion_applied": _sqlite_row_value(row, "emotion_applied"),
                        "due_time": _sqlite_row_value(row, "due_time"),
                        "due_at": _sqlite_row_value(row, "due_at"),
                        "reminder_at": _sqlite_row_value(row, "reminder_at"),
                        "reminder_method": _sqlite_row_value(row, "reminder_method"),
                        "reminder_sent": bool(_sqlite_row_value(row, "reminder_sent", 0)),
                        "reminder_last_sent_at": _sqlite_row_value(row, "reminder_last_sent_at"),
                        "reminder_phone": _sqlite_row_value(row, "reminder_phone"),
                        "created_at": _sqlite_row_value(row, "created_at"),
                        "updated_at": _sqlite_row_value(row, "updated_at"),
                    },
                )
            migrated_counts["tasks"] = len(tasks)

        if "emotion_logs" in table_names:
            logs = cur.execute("SELECT * FROM emotion_logs").fetchall()
            for row in logs:
                conn.execute(
                    text(
                        """
                        INSERT INTO emotion_logs (id, user_id, emotion, confidence, scanned_at)
                        VALUES (:id, :user_id, :emotion, :confidence, :scanned_at)
                        ON CONFLICT (id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            emotion = EXCLUDED.emotion,
                            confidence = EXCLUDED.confidence,
                            scanned_at = EXCLUDED.scanned_at
                        """
                    ),
                    {
                        "id": row["id"],
                        "user_id": row["user_id"],
                        "emotion": row["emotion"],
                        "confidence": _sqlite_row_value(row, "confidence", 0.0),
                        "scanned_at": _sqlite_row_value(row, "scanned_at"),
                    },
                )
            migrated_counts["emotion_logs"] = len(logs)

        for table_name in ["users", "tasks", "emotion_logs"]:
            conn.execute(
                text(
                    f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table_name}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                        (SELECT COUNT(*) > 0 FROM {table_name})
                    )
                    """
                )
            )

    sqlite_conn.close()
    print(
        "[MIGRATION] SQLite -> PostgreSQL sync complete: "
        f"users={migrated_counts['users']}, "
        f"tasks={migrated_counts['tasks']}, "
        f"emotion_logs={migrated_counts['emotion_logs']}"
    )


# Create database tables on startup
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    bool_default = "FALSE" if db.engine.dialect.name == "postgresql" else "0"
    if 'users' in inspector.get_table_names():
        user_columns = {c['name'] for c in inspector.get_columns('users')}
        user_alters = []
        datetime_type = "TIMESTAMP" if db.engine.dialect.name == "postgresql" else "DATETIME"
        if 'username' not in user_columns:
            user_alters.append("ALTER TABLE users ADD COLUMN username VARCHAR(80)")
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
        db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS users_username_uq ON users (username)"))
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
    sync_sqlite_to_postgres_if_enabled()
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
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1", host='localhost', port=5000)
