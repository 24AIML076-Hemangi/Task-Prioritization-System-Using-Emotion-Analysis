"""
Password Reset Routes
Handles forgot password, reset code verification, and password reset
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import secrets
import re
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# In-memory storage for reset tokens (replace with database in production)
reset_tokens = {}

# Configuration (move to environment variables in production)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'your-email@gmail.com'
SENDER_PASSWORD = 'your-app-password'  # Use app-specific password for Gmail


class ResetToken:
    """Class to manage password reset tokens"""
    def __init__(self, email):
        self.email = email
        self.code = self.generate_code()
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=1)
        self.verified = False
        self.attempts = 0
        self.max_attempts = 5

    @staticmethod
    def generate_code():
        """Generate a 6-digit verification code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

    def is_valid(self):
        """Check if token is still valid"""
        return datetime.now() < self.expires_at

    def is_code_correct(self, code):
        """Verify the reset code"""
        if self.attempts >= self.max_attempts:
            return False, "Too many attempts. Please request a new reset code."
        
        self.attempts += 1
        if self.code == code:
            self.verified = True
            return True, "Code verified successfully"
        return False, f"Invalid code. {self.max_attempts - self.attempts} attempts remaining."


def send_reset_email(email, reset_code):
    """
    Send password reset email
    Note: Configure your SMTP settings in environment variables
    """
    try:
        subject = "Password Reset Code - Task Prioritization System"
        
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h1 style="color: #333; text-align: center;">Password Reset Request</h1>
                    <p style="color: #666; font-size: 16px;">Hi,</p>
                    <p style="color: #666; font-size: 16px;">We received a request to reset your password. Use the code below to proceed:</p>
                    
                    <div style="background-color: #667eea; color: white; padding: 20px; text-align: center; border-radius: 5px; margin: 30px 0; font-size: 32px; letter-spacing: 5px; font-weight: bold;">
                        {reset_code}
                    </div>
                    
                    <p style="color: #666; font-size: 14px;">
                        <strong>This code will expire in 1 hour.</strong>
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        If you didn't request this reset, please ignore this email and your password will remain unchanged.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        Task Prioritization System | Emotion-Based Task Management
                    </p>
                </div>
            </body>
        </html>
        """
        
        # For development, just log the code
        print(f"\n{'='*50}")
        print(f"PASSWORD RESET EMAIL")
        print(f"To: {email}")
        print(f"Reset Code: {reset_code}")
        print(f"{'='*50}\n")
        
        # Uncomment below to send actual email (requires SMTP configuration)
        # message = MIMEMultipart("alternative")
        # message["Subject"] = subject
        # message["From"] = SENDER_EMAIL
        # message["To"] = email
        # message.attach(MIMEText(html_message, "html"))
        
        # with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        #     server.starttls()
        #     server.login(SENDER_EMAIL, SENDER_PASSWORD)
        #     server.sendmail(SENDER_EMAIL, email, message.as_string())
        
        return True
    
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


@auth_bp.route('/forgot-password', methods=['POST'])
@cross_origin()
def forgot_password():
    """
    Step 1: User submits email to request password reset
    Response: Returns reset token and sends code to email
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()

        # Validate email
        if not email:
            return jsonify({'message': 'Email is required'}), 400

        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return jsonify({'message': 'Invalid email format'}), 400

        # TODO: Check if email exists in database
        # For now, we'll proceed with any email
        # if not user_exists(email):
        #     return jsonify({'message': 'Email not found in system'}), 404

        # Create reset token
        reset_token = ResetToken(email)
        reset_tokens[email] = reset_token

        # Send reset code via email
        if not send_reset_email(email, reset_token.code):
            return jsonify({'message': 'Failed to send reset email'}), 500

        return jsonify({
            'message': 'Reset code sent to your email',
            'resetToken': reset_token.token,  # Return token for security
            'expiresIn': 3600  # Token expires in 1 hour
        }), 200

    except Exception as e:
        print(f"Error in forgot_password: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500


@auth_bp.route('/verify-reset-code', methods=['POST'])
@cross_origin()
def verify_reset_code():
    """
    Step 2: User submits the code received in email
    Response: Verifies code and prepares for password reset
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()

        # Validate inputs
        if not email or not code:
            return jsonify({'message': 'Email and code are required'}), 400

        # Check if reset token exists
        if email not in reset_tokens:
            return jsonify({'message': 'No reset request found for this email'}), 404

        reset_token = reset_tokens[email]

        # Check if token is still valid
        if not reset_token.is_valid():
            del reset_tokens[email]
            return jsonify({'message': 'Reset code has expired. Please request a new one.'}), 400

        # Verify the code
        is_correct, message = reset_token.is_code_correct(code)
        
        if not is_correct:
            return jsonify({'message': message}), 400

        return jsonify({
            'message': message,
            'resetToken': reset_token.token,
            'verified': True
        }), 200

    except Exception as e:
        print(f"Error in verify_reset_code: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500


@auth_bp.route('/reset-password', methods=['POST'])
@cross_origin()
def reset_password():
    """
    Step 3: User submits new password
    Response: Updates password in database
    """
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        code = data.get('code', '').strip()
        new_password = data.get('newPassword', '')

        # Validate inputs
        if not email or not code or not new_password:
            return jsonify({'message': 'Email, code, and password are required'}), 400

        # Validate password strength
        password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$'
        if not re.match(password_regex, new_password):
            return jsonify({
                'message': 'Password must contain at least 8 characters, one uppercase letter, one lowercase letter, and one number'
            }), 400

        # Check if reset token exists and is verified
        if email not in reset_tokens:
            return jsonify({'message': 'No valid reset request for this email'}), 404

        reset_token = reset_tokens[email]

        # Verify token is valid and code matches
        if not reset_token.is_valid():
            del reset_tokens[email]
            return jsonify({'message': 'Reset code has expired'}), 400

        if not reset_token.verified or reset_token.code != code:
            return jsonify({'message': 'Invalid reset code'}), 400

        # TODO: Update password in database
        # hash_password = hash_function(new_password)
        # user = User.query.filter_by(email=email).first()
        # if user:
        #     user.password = hash_password
        #     user.updated_at = datetime.now()
        #     db.session.commit()

        print(f"\n{'='*50}")
        print(f"PASSWORD RESET SUCCESSFUL")
        print(f"Email: {email}")
        print(f"New Password: {new_password}")
        print(f"{'='*50}\n")

        # Clean up reset token
        del reset_tokens[email]

        return jsonify({
            'message': 'Password has been reset successfully',
            'redirectUrl': '/login.html'
        }), 200

    except Exception as e:
        print(f"Error in reset_password: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500


@auth_bp.route('/check-reset-status', methods=['GET'])
@cross_origin()
def check_reset_status():
    """
    Check the status of password reset tokens (for admin/debugging)
    """
    try:
        status = {}
        for email, token in reset_tokens.items():
            status[email] = {
                'valid': token.is_valid(),
                'verified': token.verified,
                'attempts': token.attempts,
                'expires_at': token.expires_at.isoformat()
            }
        
        return jsonify({
            'activeResets': len(reset_tokens),
            'tokens': status
        }), 200

    except Exception as e:
        print(f"Error in check_reset_status: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500
