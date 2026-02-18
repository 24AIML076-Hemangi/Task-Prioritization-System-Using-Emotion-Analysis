"""
Database models for Task Prioritization System
"""
from datetime import datetime
from database import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """User model for authentication and task ownership"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    notification_preference = db.Column(db.String(20), default='email')  # 'email' | 'sms' | 'both'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary for JSON response (exclude password)"""
        return {
            'id': self.id,
            'email': self.email,
            'phone': self.phone,
            'notification_preference': self.notification_preference,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<User {self.id}: {self.email}>'


class Task(db.Model):
    """Task model for storing user tasks with priority and emotion data"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # Username from login
    title = db.Column(db.String(500), nullable=False)
    importance = db.Column(db.String(20), default='not-important')  # 'important' or 'not-important'
    urgency = db.Column(db.String(20), default='not-urgent')  # 'urgent' or 'not-urgent'
    completed = db.Column(db.Boolean, default=False)
    emotion_applied = db.Column(db.String(50), default=None)  # 'stressed', 'focused', 'neutral'
    due_at = db.Column(db.DateTime, default=None)
    reminder_at = db.Column(db.DateTime, default=None)
    reminder_method = db.Column(db.String(20), default=None)  # 'email' | 'sms' | 'both'
    reminder_sent = db.Column(db.Boolean, default=False)
    reminder_phone = db.Column(db.String(30), default=None)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert task to dictionary for JSON response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'importance': self.importance,
            'urgency': self.urgency,
            'completed': self.completed,
            'emotion_applied': self.emotion_applied,
            'due_at': self.due_at.isoformat() if self.due_at else None,
            'reminder_at': self.reminder_at.isoformat() if self.reminder_at else None,
            'reminder_method': self.reminder_method,
            'reminder_sent': self.reminder_sent,
            'reminder_phone': self.reminder_phone,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'


class EmotionLog(db.Model):
    """Log of emotion scans for analytics"""
    __tablename__ = 'emotion_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)
    emotion = db.Column(db.String(50), nullable=False)  # 'stressed', 'focused', 'neutral'
    confidence = db.Column(db.Float, default=0.0)  # 0-1 confidence score
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'emotion': self.emotion,
            'confidence': self.confidence,
            'scanned_at': self.scanned_at.isoformat()
        }
    
    def __repr__(self):
        return f'<EmotionLog {self.id}: {self.emotion} ({self.confidence})>'
