"""
Notification helpers for email and SMS reminders.
Falls back to console output if providers are not configured.
"""
import os
import smtplib
import random
import re
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from database import db
from models import User
from google_oauth import config_ready, refresh_access_token, send_gmail_api

PHONE_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")


def _send_with_user_gmail(owner_email, to_email, subject, body):
    if not owner_email or not config_ready():
        return False

    user = User.query.filter_by(email=owner_email).first()
    if not user or not user.gmail_connected or not user.gmail_refresh_token:
        return False

    # Refresh token if missing/expired, then send via Gmail API.
    access_token = user.gmail_access_token
    expiry = user.gmail_token_expiry
    if not access_token or not expiry or expiry <= datetime.utcnow() + timedelta(seconds=30):
        refreshed = refresh_access_token(user.gmail_refresh_token)
        if not refreshed or not refreshed.get("access_token"):
            return False
        user.gmail_access_token = refreshed["access_token"]
        user.gmail_token_expiry = refreshed.get("expires_at")
        db.session.commit()
        access_token = user.gmail_access_token

    from_email = user.gmail_email or owner_email
    return send_gmail_api(access_token, from_email, to_email, subject, body)


def send_email(to_email, subject, body, owner_email=None):
    if _send_with_user_gmail(owner_email, to_email, subject, body):
        return True

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
    host = os.getenv("SMTP_HOST") or os.getenv("SMTP_SERVER")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER") or os.getenv("SENDER_EMAIL")
    password = os.getenv("SMTP_PASS") or os.getenv("SENDER_PASSWORD")
    from_email = os.getenv("SMTP_FROM") or os.getenv("SENDER_EMAIL") or user

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


def _display_name_from_email(email):
    if not email or "@" not in email:
        return "Friend"
    local = email.split("@", 1)[0]
    cleaned = local.replace(".", " ").replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else "Friend"


def _task_type(importance=None, urgency=None):
    imp = (importance or "not-important").strip().lower()
    urg = (urgency or "not-urgent").strip().lower()
    if imp == "important" and urg == "urgent":
        return "do-now"
    if imp == "important" and urg != "urgent":
        return "plan-deep"
    if imp != "important" and urg == "urgent":
        return "delegate-fast"
    return "later-list"


def _typed_roast_line(importance=None, urgency=None):
    roast_by_type = {
        "do-now": [
            "Fire task alert: yeh abhi ka kaam hai, kal ka excuse nahi. 🔥",
            "Priority siren: important + urgent ko snooze karna risky move hai. 🚨",
            "Roast mode: deadline ko ignore karke chill? Bold strategy. 😬",
        ],
        "plan-deep": [
            "Deep-work task hai, random scrolling ka side quest mat chalu karo. 🧠",
            "Important hai but not urgent, isi phase me jeetna smart hota hai. 📌",
            "Roast mode: future-you ko panic gift mat do. 😅",
        ],
        "delegate-fast": [
            "Urgent hai but low-impact, speed rakho aur overthink mat karo. ⏱️",
            "Quick-hit task: 10 min me niptao, energy bachao. ⚡",
            "Roast mode: chhote task pe overdrama bandh. 😄",
        ],
        "later-list": [
            "Low priority task hai, but consistency ka scorecard chalta rehta hai. 📋",
            "Small task ko stack mat hone do, warna weekend hostage ban jayega. 🧱",
            "Roast mode: tiny task ko bhi trilogy mat banao. 😜",
        ],
    }
    return random.choice(roast_by_type[_task_type(importance, urgency)])


def build_reminder_content(task_title, user_email=None, importance=None, urgency=None, is_daily=False):
    """Return friendly bilingual reminder subject/body text with typed roast + emojis."""
    name = _display_name_from_email(user_email)
    task = (task_title or "Your task").strip()
    daily_tag = "Daily Reminder" if is_daily else "Task Reminder"

    openers = [
        f"Hello {name} 👋, what is your task game plan today?",
        f"Hi {name} 🌤️, aaj ka focus mode on karte hain.",
        f"Hey {name} 🙌, quick nudge for your task list.",
    ]
    nudges = [
        "Small step now, big relief later. ✅",
        "Abhi 10 minute do, baad me tension kam hogi. ⏳",
        "Consistency > perfection. Bas start karo. 🚀",
    ]

    subject = f"{daily_tag}: {task} 📝"
    body = (
        f"{random.choice(openers)}\n\n"
        f"Today task: {task} 🎯\n\n"
        f"{random.choice(nudges)}\n"
        f"{_typed_roast_line(importance, urgency)}"
    )
    return subject, body


def build_sms_reminder_content(task_title, importance=None, urgency=None, is_daily=False):
    task = (task_title or "Your task").strip()
    prefix = "Daily reminder" if is_daily else "Task reminder"
    roast = _typed_roast_line(importance, urgency)
    return f"{prefix}: {task} 📲. {roast}"


def build_empty_nudge_content(user_email=None, is_daily=True):
    name = _display_name_from_email(user_email)
    daily_tag = "Daily Check-in" if is_daily else "Check-in"
    openers = [
        f"Hello {name} 👋, hope your day is going well.",
        f"Hi {name} 🌤️, quick check-in from TaskPrioritize.",
        f"Hey {name} 🙌, sending a gentle nudge.",
    ]
    nudges = [
        "I couldn't find any tasks for today. Are you really free?",
        "No tasks found yet. If you're free, enjoy it — or add a task to stay on track.",
        "Looks like your list is empty. Want to add something small for momentum?",
    ]
    subject = f"{daily_tag}: Are you really free? 📋"
    body = f"{random.choice(openers)}\n\n{random.choice(nudges)}"
    return subject, body


def build_empty_nudge_sms(user_email=None, is_daily=True):
    name = _display_name_from_email(user_email)
    prefix = "Daily check-in" if is_daily else "Check-in"
    return f"{prefix}: Hi {name}, no tasks found today. Are you really free? 📋"


def send_sms(to_phone, body):
    to_phone = (to_phone or "").strip()
    if not PHONE_REGEX.match(to_phone):
        print(f"[sms] Invalid phone format: {to_phone}. Use E.164 format like +14155551234")
        return False

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
