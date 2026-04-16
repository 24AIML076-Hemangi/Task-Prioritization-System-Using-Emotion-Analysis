from json import load

from flask import Flask, jsonify, request, send_from_directory
import os
from dotenv import load_dotenv
from flask_cors import CORS
import sys
from sqlalchemy import inspect, text
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta

from dotenv import load_dotenv
import os 
load_dotenv()

# Add parent directory to path so we can import API module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database
from database import db
from models import User, Task, EmotionLog, UserActivityLog
from modules.emotion import preload_deepface_model

# Load .env from Backend directory before any os.getenv usage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

# Email config (SMTP)
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

print("[DEBUG] EMAIL_USER:", EMAIL_USER)
print("[DEBUG] EMAIL_PASS:", "SET" if EMAIL_PASS else "NOT SET")
if not EMAIL_USER or not EMAIL_PASS:
    print("[ERROR] Email config invalid")
else:
    print("[SUCCESS] Email config loaded")

# Resolve frontend directory and serve it from Flask so one server can host API + UI
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(project_root, "Frontend")

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

# Email configuration validation (startup)
if not EMAIL_USER or not EMAIL_PASS:
    print("[warn] Email config invalid: reminders may not send")

# Optional server-side sessions (e.g., Render + Redis)
try:
    from flask_session import Session  # type: ignore
except ImportError:
    print("[session] Flask-Session not installed; using Flask signed-cookie sessions.")
else:
    try:
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
        print(f"[session] Flask-Session enabled via {app.config.get('SESSION_TYPE', 'unknown')}.")
    except Exception as exc:
        print(f"[session] Flask-Session setup failed; using Flask signed-cookie sessions: {exc}")

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


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(frontend_dir, "logo.png", mimetype="image/png")


@app.route("/debug/users", methods=["GET"])
def debug_users():
    debug_key = os.getenv("DEBUG_KEY", "secret123")
    if request.headers.get("x-debug-key") != debug_key:
        return jsonify({"error": "Unauthorized"}), 403
    users = User.query.order_by(User.id.asc()).all()
    payload = [user.to_dict() for user in users]
    return jsonify({"count": len(payload), "users": payload}), 200

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
        if 'reminder_attempts' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_attempts INTEGER DEFAULT 0")
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

if __name__ == "__main__":
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
