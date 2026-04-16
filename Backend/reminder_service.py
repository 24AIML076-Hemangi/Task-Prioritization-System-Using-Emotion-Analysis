import logging
from datetime import datetime

from database import db
from models import Task, User
from notifications import build_reminder_content, build_welcome_content, send_email


logger = logging.getLogger(__name__)


def send_welcome_email(user_email):
    user = User.query.filter_by(email=(user_email or "").strip().lower()).first()
    if not user:
        logger.error("[welcome-email] user not found for email=%s", user_email)
        return False

    now = datetime.utcnow()
    pending_count = Task.query.filter_by(user_id=user.email, completed=False).count()
    next_task = (
        Task.query.filter_by(user_id=user.email, completed=False)
        .filter(Task.reminder_at.isnot(None))
        .filter(Task.reminder_at > now)
        .order_by(Task.reminder_at.asc())
        .first()
    )
    if next_task and next_task.reminder_at:
        time_text = next_task.reminder_at.strftime("%Y-%m-%d %H:%M UTC")
        upcoming = f"Upcoming reminder: {next_task.title} at {time_text}"
    else:
        upcoming = "No upcoming reminders."

    subject, body, is_html = build_welcome_content(
        user.email,
        pending_count=pending_count,
        upcoming=upcoming,
    )
    sent = send_email(user.email, subject, body, owner_email=user.email, is_html=is_html)
    if not sent:
        logger.error("[welcome-email] failed for user=%s", user.email)
        return False

    user.last_welcome_sent_at = now
    db.session.commit()
    logger.info("[welcome-email] sent to user=%s pending=%s", user.email, pending_count)
    return True


def send_user_reminders(user):
    if not user or not getattr(user, "email", None):
        logger.error("[reminders] skipped: invalid user object")
        return {"processed": 0, "sent": 0, "skipped": 0}

    now = datetime.utcnow()
    due_tasks = (
        Task.query.filter_by(user_id=user.email, reminder_sent=False, completed=False)
        .filter(Task.reminder_at.isnot(None))
        .filter(Task.reminder_at <= now)
        .order_by(Task.reminder_at.asc())
        .all()
    )

    if not due_tasks:
        logger.info("[reminders] skipped for user=%s: no due reminders", user.email)
        return {"processed": 0, "sent": 0, "skipped": 0}

    processed = 0
    sent_count = 0
    skipped = 0
    updated = False

    for task in due_tasks:
        processed += 1
        if not user.email:
            skipped += 1
            logger.info("[reminders] skipped task=%s for user=%s: missing email", task.id, user.email)
            continue

        subject, body = build_reminder_content(
            task.title,
            user.email,
            importance=task.importance,
            urgency=task.urgency,
            is_daily=False,
            reminder_at=task.reminder_at,
        )
        try:
            sent = send_email(user.email, subject, body, owner_email=user.email)
        except Exception as exc:
            logger.error("[reminders] error sending task=%s for user=%s: %s", task.id, user.email, exc)
            skipped += 1
            continue

        if not sent:
            logger.error("[reminders] failed to send task=%s for user=%s", task.id, user.email)
            skipped += 1
            continue

        task.reminder_sent = True
        task.reminder_last_sent_at = now
        updated = True
        sent_count += 1
        logger.info("[reminders] sent task=%s to user=%s", task.id, user.email)

    if updated:
        db.session.commit()

    return {"processed": processed, "sent": sent_count, "skipped": skipped}
