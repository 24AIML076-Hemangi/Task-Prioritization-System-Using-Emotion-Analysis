# 📝 Task Prioritization System Using Emotion Analysis

An intelligent task prioritization platform that blends an emotion-aware system with productivity optimization, helping users focus on what matters most without losing control of their workflow.

## 🔐 Project Integrity

- User control first: Manual importance/urgency always overrides emotion suggestions.
- Emotion analysis: Optional and assistive only, never diagnostic.
- Privacy-conscious: Camera is triggered only by user action.
- Transparent reminders: Falls back to console mock mode if email/SMS providers are not configured.

## ⚡ Features

- User Authentication: Signup, login, profile update, forgot/reset password
- JWT Authentication: Access + refresh token flow for protected APIs
- Task CRUD: Create, read, update, delete tasks with PostgreSQL persistence
- Priority Fields: `importance` and `urgency`
- Emotion Scan: Optional endpoint for assistive reprioritization
- Emotion Logic: Rule-based mapping between emotional states and task priority, with future scope for ML/NLP models
- Reminder Scheduling: `due_at`, `reminder_at`, delivery method, phone number
- Reminder Dispatch: Email/SMS integrations (SendGrid/Twilio or SMTP/Twilio), with safe mock fallback
- Daily Reminder Sweep: APScheduler can dispatch reminders on schedule

## 🛠️ Tech Stack

- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: Flask, Flask-SQLAlchemy, Flask-CORS
- Database: PostgreSQL (primary production database); SQLite is legacy/migration-only
- Optional AI and Notifications: DeepFace, TensorFlow, Twilio, SendGrid

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

1. Create and activate a Python virtual environment.
2. Install backend dependencies:

```bash
pip install -r Backend/requirements.txt
```

3. Configure environment variables in `.env` (copy from `.env.example`).
4. Run the backend server:

```bash
python Backend/app.py
```

5. Open the app in your browser:

- `http://localhost:5000/login.html`

## 🗄️ Database

- PostgreSQL is the primary production database.
- SQLite is supported only for legacy data migration.

## 🚀 Deployment

- Frontend: Vercel
- Backend: Render
- Database: PostgreSQL (Render)
- Live Demo: [Add frontend URL placeholder]

## 📸 Screenshots

- Login page: [Screenshot placeholder]
- Dashboard: [Screenshot placeholder]
- Task view: [Screenshot placeholder]

## 🔐 JWT Flow

1. `POST /api/auth/login` returns `access_token` and `refresh_token`.
2. Frontend sends `Authorization: Bearer <access_token>` for protected routes.
3. If access token expires, call `POST /api/auth/refresh` with refresh token.
4. Task and profile routes use JWT identity (no manual `user_id` in API calls).

## 🌐 API Summary

Below is a summarized list of available API endpoints:

Auth:

- `/api/auth/signup`
- `/api/auth/login`
- `/api/auth/forgot-password`
- `/api/auth/verify-reset-code`
- `/api/auth/reset-password`
- `/api/auth/profile`
- `/api/auth/refresh`
- `/api/auth/google-mail/status`
- `/api/auth/google-mail/start`
- `/api/auth/google-mail/callback`
- `/api/auth/google-mail/disconnect`

Tasks:

- `/api/tasks` (GET, POST)
- `/api/tasks/<id>` (PUT, DELETE)
- `/api/tasks/<id>/complete` (PATCH)

All task routes are JWT-protected.

Emotion:

- `/api/tasks/emotion-scan`
- `/api/tasks/emotion/log`

Reminders:

- `/api/tasks/reminders/dispatch`
- `/api/auth/sms/test` (JWT, sends test SMS to profile phone or provided phone)

## 💡 Future Improvements

- ML-based emotion detection
- Role-based authentication
- Real-time notifications
- UI upgrade (React)
- Analytics dashboard

## 📝 Notes

- Database schema is auto-created/migrated at backend startup.
- SMS phone format must be E.164 (example: `+14155551234`).
- Intended for learning/demo usage and can be productionized with stronger auth, migrations, and deployment hardening.
