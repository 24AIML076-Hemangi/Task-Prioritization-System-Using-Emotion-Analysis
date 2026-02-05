"""
Database models for Task Prioritization System
"""
from datetime import datetime
from database import db

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
