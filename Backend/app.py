from flask import Flask
from flask_cors import CORS
import os
import sys
from sqlalchemy import inspect, text

# Add parent directory to path so we can import API module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database
from database import db
from models import User, Task, EmotionLog

# Initialize Flask app
app = Flask(__name__)

# SQLite Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "tasks.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize Database with app
db.init_app(app)

# Enable CORS for frontend communication
CORS(app)

# Import and register routes
from API.routes import auth_bp
from task_routes import task_bp

app.register_blueprint(auth_bp)
app.register_blueprint(task_bp)

# Create database tables on startup
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    if 'tasks' in inspector.get_table_names():
        columns = {c['name'] for c in inspector.get_columns('tasks')}
        alters = []
        if 'due_at' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN due_at DATETIME")
        if 'reminder_at' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_at DATETIME")
        if 'reminder_method' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_method VARCHAR(20)")
        if 'reminder_sent' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_sent BOOLEAN DEFAULT 0")
        if 'reminder_phone' not in columns:
            alters.append("ALTER TABLE tasks ADD COLUMN reminder_phone VARCHAR(30)")
        for stmt in alters:
            db.session.execute(text(stmt))
        if alters:
            db.session.commit()
    print("Database initialized successfully!")

if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=5000)
