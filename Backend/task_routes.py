"""
Task management routes for the API
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from database import db
from models import Task, EmotionLog, User
from modules.emotion import detect_emotion_from_image, get_emotion_icon
from notifications import send_email, send_sms

task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')


def parse_datetime(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.replace(tzinfo=None)
    except Exception:
        return None

# ============ GET ALL TASKS ============
@task_bp.route('', methods=['GET'])
def get_tasks():
    """Get all tasks for the logged-in user"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([task.to_dict() for task in tasks]), 200


# ============ CREATE NEW TASK ============
@task_bp.route('', methods=['POST'])
def create_task():
    """Create a new task"""
    data = request.get_json()
    
    # Validate required fields
    if not data or 'title' not in data or 'user_id' not in data:
        return jsonify({'error': 'title and user_id are required'}), 400
    
    # Create task with defaults
    new_task = Task(
        user_id=data['user_id'],
        title=data['title'],
        importance=data.get('importance', 'not-important'),
        urgency=data.get('urgency', 'not-urgent'),
        emotion_applied=data.get('emotion_applied'),
        due_at=parse_datetime(data.get('due_at')),
        reminder_at=parse_datetime(data.get('reminder_at')),
        reminder_method=data.get('reminder_method'),
        reminder_phone=data.get('reminder_phone')
    )
    if new_task.reminder_at:
        new_task.reminder_sent = False
    
    db.session.add(new_task)
    db.session.commit()
    
    print(f"✓ Task created: {new_task.title} (ID: {new_task.id})")
    return jsonify(new_task.to_dict()), 201


# ============ UPDATE TASK ============
@task_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update an existing task"""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if 'title' in data:
        task.title = data['title']
    if 'importance' in data:
        task.importance = data['importance']
    if 'urgency' in data:
        task.urgency = data['urgency']
    if 'completed' in data:
        task.completed = data['completed']
    if 'emotion_applied' in data:
        task.emotion_applied = data['emotion_applied']
    if 'due_at' in data:
        task.due_at = parse_datetime(data.get('due_at'))
    if 'reminder_at' in data:
        task.reminder_at = parse_datetime(data.get('reminder_at'))
        task.reminder_sent = False if task.reminder_at else task.reminder_sent
    if 'reminder_method' in data:
        task.reminder_method = data.get('reminder_method')
    if 'reminder_phone' in data:
        task.reminder_phone = data.get('reminder_phone')
    
    db.session.commit()
    
    print(f"✓ Task updated: {task.title} (ID: {task_id})")
    return jsonify(task.to_dict()), 200


# ============ DELETE TASK ============
@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    
    print(f"✓ Task deleted: ID {task_id}")
    return jsonify({'message': 'Task deleted successfully'}), 200


# ============ MARK TASK COMPLETE ============
@task_bp.route('/<int:task_id>/complete', methods=['PATCH'])
def toggle_task_complete(task_id):
    """Toggle task completion status"""
    task = Task.query.get(task_id)
    
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    task.completed = not task.completed
    db.session.commit()
    
    status = "completed" if task.completed else "pending"
    print(f"✓ Task marked as {status}: {task.title}")
    return jsonify(task.to_dict()), 200


# ============ LOG EMOTION SCAN ============
@task_bp.route('/emotion/log', methods=['POST'])
def log_emotion():
    """Log an emotion scan"""
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'emotion' not in data:
        return jsonify({'error': 'user_id and emotion are required'}), 400
    
    emotion_log = EmotionLog(
        user_id=data['user_id'],
        emotion=data['emotion'],
        confidence=data.get('confidence', 0.0)
    )
    
    db.session.add(emotion_log)
    db.session.commit()
    
    print(f"✓ Emotion logged: {data['emotion']} ({data.get('confidence', 0.0)}) for {data['user_id']}")
    return jsonify(emotion_log.to_dict()), 201


# ============ EMOTION SCAN ============
@task_bp.route('/emotion-scan', methods=['POST'])
def emotion_scan():
    """Analyze emotion from image and return emotion type with confidence"""
    data = request.get_json() or {}
    
    image_base64 = data.get('image')
    user_id = data.get('user_id')
    
    if not image_base64 or not user_id:
        return jsonify({'error': 'image and user_id are required'}), 400
    
    # Detect emotion from image
    emotion_result = detect_emotion_from_image(image_base64)
    
    # Log emotion to database
    emotion_log = EmotionLog(
        user_id=user_id,
        emotion=emotion_result['emotion'],
        confidence=emotion_result['confidence']
    )
    db.session.add(emotion_log)
    db.session.commit()
    
    print(f"✓ Emotion scan: {emotion_result['emotion']} ({emotion_result['confidence']}) for {user_id}")
    
    return jsonify(emotion_result), 200


# ============ DISPATCH REMINDERS ============
@task_bp.route('/reminders/dispatch', methods=['POST'])
def dispatch_reminders():
    """Send due reminders for a user (email/SMS)"""
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    now = datetime.utcnow()
    tasks = Task.query.filter_by(user_id=user_id).all()
    due = [t for t in tasks if t.reminder_at and not t.reminder_sent and t.reminder_at <= now]

    sent = 0
    for task in due:
        user = User.query.filter_by(email=task.user_id).first()
        account_preference = (user.notification_preference if user and user.notification_preference else 'email').lower()
        method = (task.reminder_method or account_preference or 'email').lower()
        subject = f"Task Reminder: {task.title}"
        body = f"Reminder for task: {task.title}"

        ok_email = False
        ok_sms = False

        if method in ['email', 'both']:
            to_email = user.email if user else (user_id if '@' in user_id else data.get('email'))
            if to_email:
                ok_email = send_email(to_email, subject, body)

        if method in ['sms', 'both']:
            phone = task.reminder_phone or (user.phone if user else None)
            if phone:
                ok_sms = send_sms(phone, body)
            else:
                ok_sms = False

        if (method == 'email' and ok_email) or (method == 'sms' and ok_sms) or (method == 'both' and ok_email and ok_sms):
            task.reminder_sent = True
            sent += 1

    if sent:
        db.session.commit()

    return jsonify({'sent': sent, 'due': len(due)}), 200
