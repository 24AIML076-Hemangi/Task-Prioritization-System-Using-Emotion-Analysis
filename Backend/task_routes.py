"""
Task management routes for the API
"""
from flask import Blueprint, request, jsonify
from database import db
from models import Task, EmotionLog

task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

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
        emotion_applied=data.get('emotion_applied')
    )
    
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
