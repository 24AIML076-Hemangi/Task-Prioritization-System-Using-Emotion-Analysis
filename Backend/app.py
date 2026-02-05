from flask import Flask
from flask_cors import CORS
import os
import sys

# Add parent directory to path so we can import API module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import database
from database import db
from models import Task, EmotionLog

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
    print("✓ Database initialized successfully!")

if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=5000)
