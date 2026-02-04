# Forgot Password Feature - Setup

## Quick Setup (5 min)

### 1. Update `Backend/app.py`
```python
from flask_cors import CORS
from API.routes import auth_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
```

### 2. Install packages
```bash
pip install flask flask-cors python-dotenv
```

### 3. Test It
- Click "Forgot Password?" on login page
- Enter email → See code in console
- Enter 6-digit code → Reset password
- Works! ✅

---

## Files Added

**Frontend:**
- `forgot-password.html` - Password reset form
- `forgot-password-style.css` - Styling
- `forgot-password-script.js` - Logic

**Backend:**
- `API/routes.py` - API endpoints
- `Backend/reset_config.py` - Configuration

---

## How It Works

1. User clicks "Forgot Password?" → Email form
2. Enter email → Get 6-digit code (prints to console for testing)
3. Enter code → Verify code  
4. Create new password (8+ chars, uppercase, lowercase, number)
5. Success! ✅ Can login with new password

---

## API Endpoints

- `POST /api/auth/forgot-password` - Send reset code
- `POST /api/auth/verify-reset-code` - Verify code  
- `POST /api/auth/reset-password` - Update password

---

## Security Features

✅ Email verification (OTP code)
✅ Code expires after 1 hour
✅ Rate limited (5 attempts max)
✅ Strong password validation
✅ Secure token generation

---

## Testing Without Email Setup

During development, reset codes print to console:
```
==================================================
PASSWORD RESET EMAIL
To: user@example.com
Reset Code: 123456
==================================================
```

Just copy the code from console and paste it in the form!

---

## Next Steps

1. Update Flask app (add code above)
2. Install packages
3. Test in browser
4. Later: Add database + configure SMTP email
