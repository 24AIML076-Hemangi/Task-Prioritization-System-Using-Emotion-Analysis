"""
Password Reset Routes
Handles forgot password, reset code verification, and password reset
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import secrets
import re
from datetime import datetime, timedelta

# Blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# TEMP storage (college demo only)
reset_tokens = {}


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


# -------------------- ROUTES --------------------

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

    # 🔥 TODO: Update password in DB (SQLite)
    # user.password = hash(new_password)

    del reset_tokens[email]

    return jsonify({
        "message": "Password reset successful",
        "redirect": "/login.html"
    }), 200
