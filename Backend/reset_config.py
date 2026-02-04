# Configuration for Password Reset Feature
# Copy these settings to your environment variables

# Email Configuration (Gmail Example)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SENDER_EMAIL = 'your-email@gmail.com'  # Change to your email
SENDER_PASSWORD = 'your-app-password'  # Use app-specific password for Gmail

# Reset Token Settings
RESET_CODE_LENGTH = 6  # Length of verification code
RESET_CODE_EXPIRY_HOURS = 1  # Token expires in 1 hour
MAX_RESET_ATTEMPTS = 5  # Maximum attempts to enter correct code

# Security Settings
MIN_PASSWORD_LENGTH = 8
REQUIRE_PASSWORD_UPPERCASE = True
REQUIRE_PASSWORD_LOWERCASE = True
REQUIRE_PASSWORD_NUMBER = True
REQUIRE_PASSWORD_SPECIAL = False  # Set to True to require special characters


"""
To set up email sending:

1. Gmail Configuration:
   - Enable 2-Factor Authentication on your Gmail account
   - Create an App Password (https://myaccount.google.com/apppasswords)
   - Use the app password as SENDER_PASSWORD
   - Allow less secure app access (or use App Password method above)

2. Other Email Services:
   - Update SMTP_SERVER and SMTP_PORT accordingly
   - Use appropriate authentication credentials

3. Environment Variables:
   Set these in your .env file:
   
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SENDER_EMAIL=your-email@gmail.com
   SENDER_PASSWORD=your-app-password
"""
