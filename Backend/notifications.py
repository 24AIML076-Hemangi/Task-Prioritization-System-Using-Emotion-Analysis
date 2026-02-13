"""
Notification helpers for email and SMS reminders.
Falls back to console output if providers are not configured.
"""
import os
import smtplib
from email.mime.text import MIMEText


def send_email(to_email, subject, body):
    provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()

    if provider == "sendgrid":
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
        except Exception as exc:
            print(f"[email] SendGrid not available: {exc}")
            return _mock_email(to_email, subject, body)

        api_key = os.getenv("SENDGRID_API_KEY")
        from_email = os.getenv("SENDGRID_FROM")
        if not api_key or not from_email:
            return _mock_email(to_email, subject, body)

        message = Mail(from_email=from_email, to_emails=to_email, subject=subject, plain_text_content=body)
        try:
            client = SendGridAPIClient(api_key)
            client.send(message)
            return True
        except Exception as exc:
            print(f"[email] SendGrid error: {exc}")
            return False

    # Default: SMTP
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", user)

    if not host or not user or not password or not from_email:
        return _mock_email(to_email, subject, body)

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        return True
    except Exception as exc:
        print(f"[email] SMTP error: {exc}")
        return False


def send_sms(to_phone, body):
    provider = os.getenv("SMS_PROVIDER", "twilio").lower()

    if provider == "twilio":
        try:
            from twilio.rest import Client
        except Exception as exc:
            print(f"[sms] Twilio not available: {exc}")
            return _mock_sms(to_phone, body)

        sid = os.getenv("TWILIO_ACCOUNT_SID")
        token = os.getenv("TWILIO_AUTH_TOKEN")
        from_phone = os.getenv("TWILIO_FROM")

        if not sid or not token or not from_phone:
            return _mock_sms(to_phone, body)

        try:
            client = Client(sid, token)
            client.messages.create(body=body, from_=from_phone, to=to_phone)
            return True
        except Exception as exc:
            print(f"[sms] Twilio error: {exc}")
            return False

    return _mock_sms(to_phone, body)


def _mock_email(to_email, subject, body):
    print("\n=== EMAIL REMINDER (MOCK) ===")
    print("To:", to_email)
    print("Subject:", subject)
    print("Body:", body)
    print("============================\n")
    return True


def _mock_sms(to_phone, body):
    print("\n=== SMS REMINDER (MOCK) ===")
    print("To:", to_phone)
    print("Body:", body)
    print("==========================\n")
    return True
