"""
Notification helpers for email and SMS reminders.
Falls back to console output if providers are not configured.
"""
import os
import smtplib
import random
import re
from html import escape
from email.mime.text import MIMEText
from datetime import datetime

PHONE_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")


def send_email(to_email, subject, body, owner_email=None, is_html=False):
    if os.getenv("DISABLE_EMAIL", "").strip().lower() in {"1", "true", "yes", "on"}:
        print("[MOCK EMAIL] Disabled via DISABLE_EMAIL=1, skipping real send")
        return False
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
    name = _display_name_from_email(user_email)
    if reminder_at and isinstance(reminder_at, datetime):
        time_text = reminder_at.strftime("%Y-%m-%d %H:%M UTC")
    else:
        time_text = str(reminder_at) if reminder_at else "soon"
    importance_text = (importance or "not-important").replace("-", " ").title()
    urgency_text = (urgency or "not-urgent").replace("-", " ").title()
    subject = f"Reminder | {task} | {time_text}"
    body = (
        f"Hi {name},\n\n"
        f"Reminder for your task: {task} \U0001F4CC\n"
        f"Scheduled time: {time_text} \u23F0\n"
        f"Importance: {importance_text} \u2B50\n"
        f"Urgency: {urgency_text} \U0001F525\n\n"
        "A small step now can keep the rest of the day lighter. \U0001F4AA"
    )
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
    importance_text = (importance or "not-important").replace("-", " ").title()
    urgency_text = (urgency or "not-urgent").replace("-", " ").title()
    return (
        f"\U0001F514 Task reminder: {task}. "
        f"Time: {time_text}. "
        f"Importance: {importance_text}. "
        f"Urgency: {urgency_text}. "
        "\U0001F4AA"
    )


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

    subject = (
        f"{daily_tag} \U0001F31F Weekend plan?"
        if is_weekend
        else f"{daily_tag} \U0001F4DD Time to set one small goal"
    )
    if is_weekend:
        body = (
            f"{random.choice(weekend_openers)} \U0001F31E\n\n"
            f"{random.choice(weekend_nudges)} \U0001F4AA"
        )
    else:
        body = (
            f"{random.choice(weekday_openers)} \U0001F44B\n\n"
            f"{random.choice(weekday_nudges)} \u2705"
        )
    return subject, body


def build_welcome_content(user_email=None, pending_count=0, upcoming=None):
    name = _display_name_from_email(user_email)
    subject = "Welcome back to Task Prioritization System | Let's focus"
    upcoming_text = upcoming or "No upcoming reminders."
    safe_name = escape(name)
    safe_upcoming = escape(upcoming_text)
    task_label = "task" if pending_count == 1 else "tasks"
    body = (
        "<div style=\"font-family:Arial,sans-serif;line-height:1.6;background:#f4efe6;padding:24px;\">"
        "<div style=\"max-width:560px;margin:0 auto;background:#ffffff;border-radius:18px;padding:28px;"
        "border:1px solid #eadfce;box-shadow:0 10px 30px rgba(76, 55, 33, 0.08);\">"
        "<div style=\"font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#9a6b2f;"
        "font-weight:700;margin-bottom:12px;\">Daily Focus Check-In</div>"
        f"<p style=\"margin:0 0 12px;font-size:18px;color:#2f2419;\"><strong>Hi {safe_name}</strong> &#128075;</p>"
        "<div style=\"background:#fff6e8;border:1px solid #f0d7ab;border-radius:14px;padding:16px 18px;"
        "margin:0 0 16px;\">"
        "<div style=\"font-size:13px;color:#9a6b2f;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;\">"
        "Pending Tasks</div>"
        f"<div style=\"font-size:32px;font-weight:800;color:#2f2419;margin-top:6px;\">{pending_count}</div>"
        f"<div style=\"font-size:15px;color:#5f4630;\">You currently have {pending_count} pending {task_label} &#128221;</div>"
        "</div>"
        "<div style=\"background:#f8fafc;border:1px solid #d9e2ec;border-radius:14px;padding:16px 18px;"
        "margin:0 0 18px;\">"
        "<div style=\"font-size:13px;color:#486581;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;\">"
        "Next Reminder</div>"
        f"<div style=\"font-size:15px;color:#243b53;margin-top:8px;\">{safe_upcoming} &#9200;</div>"
        "</div>"
        "<p style=\"margin:0;font-size:15px;color:#3e2f22;\">"
        "You've got this. One clear task at a time &#128170;"
        "</p>"
        "</div>"
        "</div>"
    )
    return subject, body, True


def build_empty_nudge_sms(user_email=None, is_daily=True):
    name = _display_name_from_email(user_email)
    prefix = "Daily check-in" if is_daily else "Check-in"
    return (
        f"{prefix} \U0001F4DD: Hi {name}, no tasks found today. "
        "Add one small task and build momentum \U0001F4AA"
    )


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
