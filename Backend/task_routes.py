"""
Task management routes for the API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import re
import os
import logging
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db
from models import Task, EmotionLog, User
from modules.emotion import (
    detect_emotion_from_image,
    normalize_emotion_label,
    ALLOWED_EMOTIONS,
)
from notifications import send_email, send_sms, build_reminder_content, build_sms_reminder_content
from activity_logger import log_activity


task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')
logger = logging.getLogger(__name__)
PHONE_REGEX = re.compile(r"^\+[1-9]\d{7,14}$")
PHONE_COUNTRY_REGEX = re.compile(r"^\+[1-9]\d{0,3}$")
DEFAULT_PHONE_COUNTRY = "+91"


def normalize_phone(phone_value, phone_country=DEFAULT_PHONE_COUNTRY):
    raw = str(phone_value or '').strip()
    if not raw:
        return None

    if raw.startswith('+'):
        candidate = '+' + re.sub(r'\D', '', raw[1:])
    else:
        digits = re.sub(r'\D', '', raw)
        country = str(phone_country or DEFAULT_PHONE_COUNTRY).strip()
        if not PHONE_COUNTRY_REGEX.match(country):
            country = DEFAULT_PHONE_COUNTRY
        candidate = f"{country}{digits}"

    return candidate if PHONE_REGEX.match(candidate) else None


def parse_datetime(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.replace(tzinfo=None)
    except Exception:
        return None


def parse_time(value):
    if not value:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%H:%M").time()
    except Exception:
        try:
            return datetime.strptime(raw, "%H:%M:%S").time()
        except Exception:
            return None


def merge_date_time(date_value, time_value):
    if not time_value:
        return None
    base_date = date_value.date() if date_value else datetime.utcnow().date()
    return datetime.combine(base_date, time_value)


def get_current_user_id():
    return get_jwt_identity()


def get_owned_task(task_id, user_id):
    task = Task.query.get(task_id)
    if not task:
        return None, (jsonify({'error': 'Task not found'}), 404)
    if task.user_id != user_id:
        return None, (jsonify({'error': 'Unauthorized'}), 403)
    return task, None


@task_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get all tasks for the logged-in user"""
    user_id = get_current_user_id()
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([task.to_dict() for task in tasks]), 200


@task_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task"""
    data = request.get_json() or {}
    user_id = get_current_user_id()

    if 'title' not in data or not str(data.get('title', '')).strip():
        return jsonify({'error': 'title is required'}), 400

    raw_reminder_phone = str(data.get('reminder_phone') or '').strip()
    reminder_phone_country = str(data.get('reminder_phone_country', DEFAULT_PHONE_COUNTRY)).strip() or DEFAULT_PHONE_COUNTRY
    reminder_phone = normalize_phone(raw_reminder_phone, reminder_phone_country)
    if raw_reminder_phone and not reminder_phone:
        return jsonify({'error': 'Invalid reminder_phone. Enter local digits with country code, or full E.164'}), 400

    emotion_applied = None
    if 'emotion_applied' in data and data.get('emotion_applied') is not None:
        emotion_applied = normalize_emotion_label(data.get('emotion_applied'))

    due_time = parse_time(data.get('due_time'))
    due_at = parse_datetime(data.get('due_at'))

    new_task = Task(
        user_id=user_id,
        title=str(data['title']).strip(),
        importance=data.get('importance', 'not-important'),
        urgency=data.get('urgency', 'not-urgent'),
        emotion_applied=emotion_applied,
        due_at=due_at,
        due_time=due_time,
        reminder_at=parse_datetime(data.get('reminder_at')),
        reminder_method=data.get('reminder_method'),
        reminder_phone=reminder_phone
    )
    if not new_task.reminder_at and due_time:
        new_task.reminder_at = merge_date_time(due_at, due_time)
    if new_task.reminder_at:
        new_task.reminder_sent = False

    db.session.add(new_task)
    db.session.commit()

    detail_parts = [f"id={new_task.id}", f"title={new_task.title}"]
    if new_task.due_time:
        detail_parts.append(f"due_time={new_task.due_time.strftime('%H:%M')}")
    log_activity(user_id, "task_created", ", ".join(detail_parts))
    print(f"Task created: {new_task.title} (ID: {new_task.id})")
    return jsonify(new_task.to_dict()), 201


@task_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update an existing task"""
    user_id = get_current_user_id()
    task, error = get_owned_task(task_id, user_id)
    if error:
        return error

    data = request.get_json() or {}

    if 'title' in data:
        task.title = data['title']
    if 'importance' in data:
        task.importance = data['importance']
    if 'urgency' in data:
        task.urgency = data['urgency']
    if 'completed' in data:
        task.completed = data['completed']
        if task.completed:
            # Completing a task cancels reminder dispatch for that task.
            task.reminder_sent = True
    if 'emotion_applied' in data:
        task.emotion_applied = normalize_emotion_label(data.get('emotion_applied'))
    if 'due_at' in data:
        task.due_at = parse_datetime(data.get('due_at'))
    if 'due_time' in data:
        task.due_time = parse_time(data.get('due_time'))
    if 'reminder_at' in data:
        task.reminder_at = parse_datetime(data.get('reminder_at'))
        task.reminder_sent = False if task.reminder_at else task.reminder_sent
        task.reminder_last_sent_at = None
    if 'reminder_method' in data:
        task.reminder_method = data.get('reminder_method')
    if 'reminder_phone' in data:
        raw_reminder_phone = str(data.get('reminder_phone') or '').strip()
        reminder_phone_country = str(data.get('reminder_phone_country', DEFAULT_PHONE_COUNTRY)).strip() or DEFAULT_PHONE_COUNTRY
        reminder_phone = normalize_phone(raw_reminder_phone, reminder_phone_country)
        if raw_reminder_phone and not reminder_phone:
            return jsonify({'error': 'Invalid reminder_phone. Enter local digits with country code, or full E.164'}), 400
        task.reminder_phone = reminder_phone

    if not task.reminder_at and task.due_time:
        task.reminder_at = merge_date_time(task.due_at, task.due_time)
        task.reminder_sent = False if task.reminder_at else task.reminder_sent

    db.session.commit()

    log_activity(user_id, "task_updated", f"id={task.id}, title={task.title}")
    print(f"Task updated: {task.title} (ID: {task_id})")
    return jsonify(task.to_dict()), 200


@task_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    user_id = get_current_user_id()
    task, error = get_owned_task(task_id, user_id)
    if error:
        return error

    db.session.delete(task)
    db.session.commit()

    print(f"Task deleted: ID {task_id}")
    return jsonify({'message': 'Task deleted successfully'}), 200


@task_bp.route('/<int:task_id>/complete', methods=['PATCH'])
@jwt_required()
def toggle_task_complete(task_id):
    """Toggle task completion status"""
    user_id = get_current_user_id()
    task, error = get_owned_task(task_id, user_id)
    if error:
        return error

    task.completed = not task.completed
    if task.completed:
        task.reminder_sent = True
    elif task.reminder_at:
        task.reminder_sent = False
    db.session.commit()

    status = 'completed' if task.completed else 'pending'
    log_activity(user_id, "task_updated", f"id={task.id}, status={status}, title={task.title}")
    print(f"Task marked as {status}: {task.title}")
    return jsonify(task.to_dict()), 200


@task_bp.route('/emotion/log', methods=['POST'])
@jwt_required()
def log_emotion():
    """Log an emotion scan for the authenticated user"""
    data = request.get_json() or {}
    raw_emotion = data.get('emotion')
    if not raw_emotion:
        return jsonify({'error': 'emotion is required'}), 400
    emotion = normalize_emotion_label(raw_emotion)
    if emotion not in ALLOWED_EMOTIONS:
        return jsonify({'error': f'Invalid emotion. Allowed: {sorted(ALLOWED_EMOTIONS)}'}), 400

    user_id = get_current_user_id()
    emotion_log = EmotionLog(
        user_id=user_id,
        emotion=emotion,
        confidence=data.get('confidence', 0.0)
    )

    db.session.add(emotion_log)
    db.session.commit()

    log_activity(user_id, "emotion_log", f"emotion={emotion_log.emotion}, confidence={emotion_log.confidence}")
    return jsonify(emotion_log.to_dict()), 201


@task_bp.route('/emotion-scan', methods=['POST'])
@jwt_required()
def emotion_scan():
    """Analyze emotion from image and return emotion type with confidence"""
    data = request.get_json() or {}
    image_base64 = data.get('image')
    user_id = get_current_user_id()

    if not image_base64:
        return jsonify({'error': 'image is required'}), 400

    try:
        emotion_result = detect_emotion_from_image(image_base64)
    except Exception as exc:
        logger.exception("Emotion scan failed, using neutral fallback: %s", exc)
        emotion_result = {
            "emotion": "neutral",
            "confidence": 0.6,
            "message": "Emotion scan unavailable. Using neutral fallback.",
            "debug": {
                "source": "error",
                "dominant_emotion": "neutral",
                "scores": {},
            },
        }
    emotion_result["emotion"] = normalize_emotion_label(emotion_result.get("emotion"))
    print("Emotion result:", emotion_result)

    emotion_log = EmotionLog(
        user_id=user_id,
        emotion=emotion_result['emotion'],
        confidence=emotion_result['confidence']
    )
    db.session.add(emotion_log)
    db.session.commit()

    log_activity(
        user_id,
        "emotion_scan",
        f"emotion={emotion_result['emotion']}, confidence={emotion_result['confidence']}",
    )
    return jsonify(emotion_result), 200


@task_bp.route('/reminders/dispatch', methods=['POST'])
@jwt_required()
def dispatch_reminders():
    """Send due reminders for the authenticated user (email/SMS)"""
    user_id = get_current_user_id()
    now = datetime.utcnow()
    cooldown_minutes = int(os.getenv("REMINDER_COOLDOWN_MINUTES", "30"))
    max_per_run = int(os.getenv("REMINDER_MAX_PER_USER_PER_RUN", "5"))

    tasks = Task.query.filter_by(user_id=user_id).all()
    due = [t for t in tasks if t.reminder_at and not t.reminder_sent and t.reminder_at <= now and not t.completed]

    user = User.query.filter_by(email=user_id).first()
    sent = 0

    for task in due:
        if sent >= max_per_run:
            break
        if task.reminder_last_sent_at and now - task.reminder_last_sent_at < timedelta(minutes=cooldown_minutes):
            continue

        account_preference = (user.notification_preference if user and user.notification_preference else 'email').lower()
        method = (task.reminder_method or account_preference or 'email').lower()

        ok_email = False
        ok_sms = False
        to_email = user.email if user else (user_id if '@' in user_id else None)
        phone = task.reminder_phone or (user.phone if user else None)
        email_attemptable = bool(to_email) if method in ['email', 'both'] else False
        sms_attemptable = bool(phone and PHONE_REGEX.match(phone)) if method in ['sms', 'both'] else False

        if method in ['email', 'both'] and email_attemptable:
            subject, body = build_reminder_content(
                task.title,
                to_email,
                importance=task.importance,
                urgency=task.urgency,
                is_daily=False,
            )
            ok_email = send_email(to_email, subject, body, owner_email=user_id)

        if method in ['sms', 'both'] and sms_attemptable:
            ok_sms = send_sms(
                phone,
                build_sms_reminder_content(
                    task.title,
                    importance=task.importance,
                    urgency=task.urgency,
                    is_daily=False,
                ),
            )

        delivery_satisfied = (
            (method == 'email' and ok_email)
            or (method == 'sms' and ok_sms)
            or (method == 'both' and (ok_email or ok_sms))
        )
        terminal_misconfig = (
            (method == 'email' and not email_attemptable)
            or (method == 'sms' and not sms_attemptable)
            or (method == 'both' and not email_attemptable and not sms_attemptable)
        )
        if delivery_satisfied or terminal_misconfig:
            task.reminder_sent = True
            task.reminder_last_sent_at = now
            sent += 1

    if sent:
        db.session.commit()

    return jsonify({'sent': sent, 'due': len(due)}), 200
