"""
Notification helpers for email and SMS reminders.
Falls back to console output if providers are not configured.
"""
import os
import smtplib
import random
import re
from email.mime.text import MIMEText
from datetime import datetime

PHONE_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")


def send_email(to_email, subject, body, owner_email=None, is_html=False):
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    if not email_user or not email_pass:
        print("[MOCK EMAIL] Config missing, skipping real send")
        return False

    try:
        msg = MIMEText(body, "html" if is_html else "plain")
        msg["Subject"] = subject
        msg["From"] = email_user
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, to_email, msg.as_string())
        server.quit()

        print(f"[EMAIL] Sent to {to_email}")
        return True
    except Exception as exc:
        print(f"[EMAIL ERROR] {exc}")
        return False


def _display_name_from_email(email):
    if not email or "@" not in email:
        return "Friend"
    local = email.split("@", 1)[0]
    cleaned = local.replace(".", " ").replace("_", " ").replace("-", " ").strip()
    return cleaned.title() if cleaned else "Friend"


def build_reminder_content(
    task_title,
    user_email=None,
    importance=None,
    urgency=None,
    is_daily=False,
    reminder_at=None,
):
    task = (task_title or "Your task").strip()
    if reminder_at and isinstance(reminder_at, datetime):
        time_text = reminder_at.strftime("%Y-%m-%d %H:%M UTC")
    else:
        time_text = str(reminder_at) if reminder_at else "soon"
    subject = f"Reminder: {task}"
    body = f"Reminder: Complete your task '{task}' at {time_text}"
    return subject, body


def build_sms_reminder_content(
    task_title,
    importance=None,
    urgency=None,
    is_daily=False,
    reminder_at=None,
):
    task = (task_title or "Your task").strip()
    if reminder_at and isinstance(reminder_at, datetime):
        time_text = reminder_at.strftime("%Y-%m-%d %H:%M UTC")
    else:
        time_text = str(reminder_at) if reminder_at else "soon"
    return f"Reminder: Complete your task '{task}' at {time_text}"


def build_empty_nudge_content(user_email=None, is_daily=True):
    name = _display_name_from_email(user_email)
    daily_tag = "Daily Check-in" if is_daily else "Check-in"
    is_weekend = False
    try:
        is_weekend = datetime.utcnow().weekday() >= 5
    except Exception:
        is_weekend = False

    weekday_openers = [
        f"Hello {name}, quick check-in.",
        f"Hi {name}, small nudge to plan your day.",
        f"Hey {name}, ready to add a task?",
    ]
    weekday_nudges = [
        "No tasks found today. Add one small task to build momentum.",
        "Your list is empty. Start with a quick win.",
        "Tiny tasks add up. Add one now.",
    ]

    weekend_openers = [
        f"Hello {name}, weekend check-in.",
        f"Hi {name}, weekend plan set?",
        f"Hey {name}, weekend vibe on?",
    ]
    weekend_nudges = [
        "Weekend tasks are empty. Add a light plan for balance.",
        "No weekend tasks yet. A small plan helps Monday.",
        "Enjoy your weekend, or add a tiny task to stay steady.",
    ]

    subject = f"{daily_tag}: Weekend plan?" if is_weekend else f"{daily_tag}: Are you really free?"
    if is_weekend:
        body = f"{random.choice(weekend_openers)}\n\n{random.choice(weekend_nudges)}"
    else:
        body = f"{random.choice(weekday_openers)}\n\n{random.choice(weekday_nudges)}"
    return subject, body


def build_welcome_content(user_email=None, pending_count=0, upcoming=None):
    name = _display_name_from_email(user_email)
    subject = "Welcome back to Task Prioritization System"
    upcoming_text = upcoming or "No upcoming reminders."
    body = (
        "<div style=\"font-family:Arial,sans-serif;line-height:1.5;\">"
        f"<p>Hi {name},</p>"
        f"<p>You have {pending_count} pending tasks.</p>"
        f"<p>{upcoming_text}</p>"
        "<p>Have a focused day!</p>"
        "</div>"
    )
    return subject, body, True


def build_empty_nudge_sms(user_email=None, is_daily=True):
    name = _display_name_from_email(user_email)
    prefix = "Daily check-in" if is_daily else "Check-in"
    return f"{prefix}: Hi {name}, no tasks found today. Are you really free?"


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


def _mock_sms(to_phone, body):
    print("\n=== SMS REMINDER (MOCK) ===")
    print("To:", to_phone)
    print("Body:", body)
    print("==========================\n")
    return True
