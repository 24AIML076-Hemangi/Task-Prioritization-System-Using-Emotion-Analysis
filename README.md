# 📝 Task Prioritization System Using Emotion Analysis 😎💡

A full-stack task management app that combines manual prioritization (Eisenhower Matrix) with optional emotion-assisted task ordering. Organize smarter, work faster, and let your emotions guide, but never control, your workflow.

## 🔐 Project Integrity

- User control first: Manual importance/urgency always overrides emotion suggestions. 🕹️
- Emotion analysis: Optional and assistive only, never diagnostic. 🤖💭
- Privacy-conscious: Camera is triggered only by user action. 📸
- Transparent reminders: Falls back to console mock mode if email/SMS providers are not configured. 📬

## ⚡ Features

- User Authentication: Signup, login, profile update, forgot/reset password 🔑
- Task CRUD: Create, read, update, delete tasks with SQLite persistence 💾
- Priority Fields: `importance` and `urgency` 🏷️
- Emotion Scan: Optional endpoint for assistive reprioritization 🎭
- Reminder Scheduling: `due_at`, `reminder_at`, delivery method, phone number ⏰📱
- Reminder Dispatch: Email/SMS integrations (SendGrid/Twilio or SMTP/Twilio), with safe mock fallback 🚨

## 🛠️ Tech Stack

- Frontend: HTML, CSS, Vanilla JavaScript 🌐
- Backend: Flask, Flask-SQLAlchemy, Flask-CORS 🔧
- Database: SQLite 🗄️
- Optional AI and Notifications: DeepFace, TensorFlow, Twilio, SendGrid 🤖💌

## 📂 Project Structure

```text
.
|-- Frontend/
|   |-- login.html
|   |-- signup.html
|   |-- forgot-password.html
|   |-- dashboard.html
|   |-- *.css / *.js
|-- Backend/
|   |-- app.py
|   |-- task_routes.py
|   |-- models.py
|   |-- notifications.py
|   |-- requirements.txt
|   `-- modules/
|       |-- emotion.py
|       `-- task.py
|-- API/
|   `-- routes.py
|-- Data_Storage/
|-- .env.example
`-- README.md
```

## ⚙️ Setup

1. Create and activate a Python virtual environment 🐍
2. Install backend dependencies:

```bash
pip install -r Backend/requirements.txt
```

3. Configure environment variables in `.env` (copy from `.env.example`) ⚙️
4. Run the backend server:

```bash
python Backend/app.py
```

5. Open the app in your browser:

- `http://localhost:5000/login.html`

## 🌐 API Summary

Auth:

- `/api/auth/signup`
- `/api/auth/login`
- `/api/auth/forgot-password`
- `/api/auth/verify-reset-code`
- `/api/auth/reset-password`
- `/api/auth/profile`

Tasks:

- `/api/tasks` (GET, POST)
- `/api/tasks/<id>` (PUT, DELETE)
- `/api/tasks/<id>/complete` (PATCH)

Emotion:

- `/api/tasks/emotion-scan`
- `/api/tasks/emotion/log`

Reminders:

- `/api/tasks/reminders/dispatch` 📩

## 📝 Notes

- Database schema is auto-created/migrated at backend startup ⚡
- Intended for learning/demo usage. Can be productionized with:
- Stronger auth/session controls 🔒
- Migration tooling 🛠️
- Deployment hardening 🚀
