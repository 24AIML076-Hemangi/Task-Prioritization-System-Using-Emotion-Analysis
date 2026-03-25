import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from database import db
from models import UserActivityLog


_LOG_PATH = os.path.join(os.path.dirname(__file__), "logs.txt")
_LOGGER = logging.getLogger("activity_logger")

if not _LOGGER.handlers:
    _LOGGER.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        _LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    _LOGGER.addHandler(handler)
    _LOGGER.propagate = False


def log_activity(user_identifier, action, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_value = user_identifier or "unknown"
    message = f"[{timestamp}] | USER: {user_value} | ACTION: {action}"
    if details:
        message = f"{message} | DETAILS: {details}"
    _LOGGER.info(message)
    try:
        record = UserActivityLog(
            user_email=user_identifier,
            action=action,
            details=details,
        )
        db.session.add(record)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        _LOGGER.error("DB log insert failed: %s", exc)
