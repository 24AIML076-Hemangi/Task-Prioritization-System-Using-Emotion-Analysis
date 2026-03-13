"""
Password Reset Routes
Handles forgot password, reset code verification, and password reset
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)
import secrets
import re
from datetime import datetime, timedelta
import sys
import os

# Import database and User model
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import db
from models import User
from google_oauth import (
    build_auth_url,
    config_ready,
    exchange_code_for_tokens,
    fetch_google_email,
)
from notifications import send_sms

# Blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# TEMP storage (college demo only)
reset_tokens = {}
oauth_states = {}
PHONE_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")
PHONE_COUNTRY_REGEX = re.compile(r"^\+[1-9]\d{0,3}$")
DEFAULT_PHONE_COUNTRY = "+91"


def normalize_phone(phone_value, phone_country=DEFAULT_PHONE_COUNTRY):
    raw = str(phone_value or "").strip()
    if not raw:
        return None

    if raw.startswith("+"):
        candidate = "+" + re.sub(r"\D", "", raw[1:])
    else:
        digits = re.sub(r"\D", "", raw)
        country = str(phone_country or DEFAULT_PHONE_COUNTRY).strip()
        if not PHONE_COUNTRY_REGEX.match(country):
            country = DEFAULT_PHONE_COUNTRY
        candidate = f"{country}{digits}"

    return candidate if PHONE_REGEX.match(candidate) else None


class ResetToken:
    def __init__(self, email):
        self.email = email
        self.code = self._generate_code()
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=1)
        self.verified = False
        self.attempts = 0
        self.max_attempts = 5

    def _generate_code(self):
        return "".join(str(secrets.randbelow(10)) for _ in range(6))

    def is_valid(self):
        return datetime.now() < self.expires_at

    def verify_code(self, code):
        if self.attempts >= self.max_attempts:
            return False, "Too many attempts. Request a new code."

        self.attempts += 1

        if self.code == code:
            self.verified = True
            return True, "Code verified successfully"

        return False, f"Invalid code. Attempts left: {self.max_attempts - self.attempts}"


def mock_send_email(email, code):
    """Mock email sender for college demo"""
    print("\n========== PASSWORD RESET ==========")
    print("To:", email)
    print("Reset Code:", code)
    print("===================================\n")
    return True


def _clear_expired_oauth_states():
    now = datetime.utcnow()
    expired = [k for k, v in oauth_states.items() if v.get("expires_at") and v["expires_at"] < now]
    for key in expired:
        del oauth_states[key]


# -------------------- ROUTES --------------------

@auth_bp.route("/signup", methods=["POST"])
@cross_origin()
def signup():
    """Register a new user"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    raw_phone = str(data.get("phone", "")).strip()
    phone_country = str(data.get("phone_country", DEFAULT_PHONE_COUNTRY)).strip() or DEFAULT_PHONE_COUNTRY
    phone = normalize_phone(raw_phone, phone_country)
    notification_preference = (data.get("notification_preference", "email") or "email").strip().lower()

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email format"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400

    if notification_preference not in ["email", "sms", "both"]:
        return jsonify({"error": "Invalid notification preference"}), 400
    if raw_phone and not phone:
        return jsonify({"error": "Invalid phone. Enter local digits with country code, or full E.164"}), 400
    if notification_preference in ["sms", "both"] and not phone:
        return jsonify({"error": "Phone number required for SMS notifications"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "Email already registered"}), 400

    new_user = User(email=email, phone=phone, notification_preference=notification_preference)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    print(f"User registered: {email}")
    return jsonify(new_user.to_dict()), 201


@auth_bp.route("/login", methods=["POST"])
@cross_origin()
def login():
    """Authenticate user and return JWT tokens"""
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.email)
    refresh_token = create_refresh_token(identity=user.email)

    print(f"User logged in: {email}")
    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }), 200


@auth_bp.route("/refresh", methods=["POST"])
@cross_origin()
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify({"access_token": access_token, "token_type": "Bearer"}), 200


@auth_bp.route("/profile", methods=["GET"])
@cross_origin()
@jwt_required()
def get_profile():
    email = get_jwt_identity()

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route("/profile", methods=["PUT"])
@cross_origin()
@jwt_required()
def update_profile():
    data = request.get_json() or {}
    email = get_jwt_identity()

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    normalized_phone = None
    if "phone" in data:
        raw_phone = str(data.get("phone") or "").strip()
        phone_country = str(data.get("phone_country", DEFAULT_PHONE_COUNTRY)).strip() or DEFAULT_PHONE_COUNTRY
        normalized_phone = normalize_phone(raw_phone, phone_country)
        if raw_phone and not normalized_phone:
            return jsonify({"error": "Invalid phone. Enter local digits with country code, or full E.164"}), 400
        user.phone = normalized_phone

    if "notification_preference" in data:
        preference = (data.get("notification_preference") or "email").strip().lower()
        if preference not in ["email", "sms", "both"]:
            return jsonify({"error": "Invalid notification preference"}), 400
        effective_phone = normalized_phone if "phone" in data else user.phone
        if preference in ["sms", "both"] and not effective_phone:
            return jsonify({"error": "Phone number required for SMS notifications"}), 400
        user.notification_preference = preference

    db.session.commit()
    return jsonify(user.to_dict()), 200


@auth_bp.route("/sms/test", methods=["POST"])
@cross_origin()
@jwt_required()
def send_test_sms():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}
    raw_phone = str(data.get("phone") or "").strip()
    if raw_phone:
        phone_country = str(data.get("phone_country", DEFAULT_PHONE_COUNTRY)).strip() or DEFAULT_PHONE_COUNTRY
        phone = normalize_phone(raw_phone, phone_country)
        if not phone:
            return jsonify({"error": "Invalid phone. Enter local digits with country code, or full E.164"}), 400
    else:
        phone = (user.phone or "").strip()
    if not phone:
        return jsonify({"error": "Phone number is required"}), 400
    if not PHONE_REGEX.match(phone):
        return jsonify({"error": "Phone must be in E.164 format, e.g. +14155551234"}), 400

    ok = send_sms(phone, "TaskPrioritize test SMS: your SMS reminders are configured.")
    if not ok:
        return jsonify({"error": "SMS provider not configured or delivery failed"}), 400
    return jsonify({"message": "Test SMS sent", "phone": phone}), 200


@auth_bp.route("/google-mail/status", methods=["GET"])
@cross_origin()
@jwt_required()
def google_mail_status():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    connected = bool(user.gmail_connected and user.gmail_refresh_token)
    return jsonify({
        "connected": connected,
        "gmail_email": user.gmail_email,
        "oauth_configured": config_ready(),
    }), 200


@auth_bp.route("/google-mail/start", methods=["POST"])
@cross_origin()
@jwt_required()
def google_mail_start():
    if not config_ready():
        return jsonify({"error": "Google OAuth is not configured on server"}), 400

    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    _clear_expired_oauth_states()
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "email": user.email,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
    }
    return jsonify({"auth_url": build_auth_url(state)}), 200


@auth_bp.route("/google-mail/callback", methods=["GET"])
@cross_origin()
def google_mail_callback():
    state = request.args.get("state", "").strip()
    code = request.args.get("code", "").strip()
    error = request.args.get("error", "").strip()

    if error:
        return f"Google OAuth failed: {error}", 400
    if not state or not code:
        return "Missing state or code", 400

    _clear_expired_oauth_states()
    pending = oauth_states.pop(state, None)
    if not pending:
        return "Invalid or expired OAuth state", 400

    user = User.query.filter_by(email=pending["email"]).first()
    if not user:
        return "User not found", 404

    token_data = exchange_code_for_tokens(code)
    if not token_data:
        return "Token exchange failed", 400

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    if not access_token or not refresh_token:
        return "Google did not return required tokens. Try reconnect with consent again.", 400

    gmail_email = fetch_google_email(access_token) or user.email
    user.gmail_connected = True
    user.gmail_email = gmail_email
    user.gmail_access_token = access_token
    user.gmail_refresh_token = refresh_token
    user.gmail_token_expiry = token_data.get("expires_at")
    user.gmail_scope = token_data.get("scope")
    db.session.commit()

    return (
        "<html><body><h3>Gmail connected successfully.</h3>"
        "<script>window.close && window.close();</script></body></html>",
        200,
    )


@auth_bp.route("/google-mail/disconnect", methods=["POST"])
@cross_origin()
@jwt_required()
def google_mail_disconnect():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.gmail_connected = False
    user.gmail_email = None
    user.gmail_access_token = None
    user.gmail_refresh_token = None
    user.gmail_token_expiry = None
    user.gmail_scope = None
    db.session.commit()
    return jsonify({"message": "Gmail sender disconnected"}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
@cross_origin()
def forgot_password():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({"error": "Invalid email format"}), 400

    reset_token = ResetToken(email)
    reset_tokens[email] = reset_token

    mock_send_email(email, reset_token.code)

    return jsonify({
        "message": "Reset code sent to email",
        "resetToken": reset_token.token,
        "expiresIn": 3600
    }), 200


@auth_bp.route("/verify-reset-code", methods=["POST"])
@cross_origin()
def verify_reset_code():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()

    if not email or not code:
        return jsonify({"error": "Email and code required"}), 400

    token = reset_tokens.get(email)
    if not token:
        return jsonify({"error": "No reset request found"}), 404

    if not token.is_valid():
        del reset_tokens[email]
        return jsonify({"error": "Reset code expired"}), 400

    ok, msg = token.verify_code(code)
    if not ok:
        return jsonify({"error": msg}), 400

    return jsonify({
        "message": msg,
        "verified": True
    }), 200


@auth_bp.route("/reset-password", methods=["POST"])
@cross_origin()
def reset_password():
    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    new_password = data.get("newPassword", "")

    if not all([email, code, new_password]):
        return jsonify({"error": "All fields are required"}), 400

    if not re.match(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$", new_password):
        return jsonify({"error": "Weak password"}), 400

    token = reset_tokens.get(email)
    if not token or not token.is_valid():
        return jsonify({"error": "Invalid or expired reset request"}), 400

    if not token.verified or token.code != code:
        return jsonify({"error": "Invalid reset code"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.set_password(new_password)
    db.session.commit()

    print(f"Password reset for: {email}")
    del reset_tokens[email]

    return jsonify({
        "message": "Password reset successful",
        "redirect": "/login.html"
    }), 200
