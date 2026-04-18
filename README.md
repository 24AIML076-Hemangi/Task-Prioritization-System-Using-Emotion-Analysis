# Task Prioritization System Using Emotion Analysis

> Plan smarter. Stay calmer. Prioritize with clarity. ✅🧠📌

An intelligent task management web app that combines classic prioritization methods with optional emotion-aware suggestions. The system helps users manage tasks, set reminders, receive email or SMS notifications, and use a one-time camera scan to get supportive task recommendations without taking control away from the user.

## 🌟 What This Project Does

This project is built to help users:

- 📝 create and manage tasks in a clean dashboard
- 🎯 prioritize work using matrices like Eisenhower, Impact vs Effort, and MoSCoW
- 🧠 optionally scan current emotion and get supportive task suggestions
- ⏰ set reminders for deadlines and upcoming work
- 📧 receive reminder emails
- 📱 receive SMS reminders and send test SMS messages
- 🔐 use secure JWT-based authentication with refresh tokens
- 📩 connect Gmail OAuth for sender-related workflow support
- 📊 track activity logs for actions like login, task creation, updates, and emotion scans

## ✨ Core Highlights

- 🔐 Signup, login, forgot password, reset password, profile update
- 🔁 Access token + refresh token flow
- 📋 Full task CRUD with completion toggle
- 🗂️ Task grouping with dashboard views like Today, Next 7 Days, Inbox, Work, Study, Personal
- 📐 Multiple prioritization matrices in the frontend
- 📷 Optional 5-second camera-based emotion scan
- 💡 Emotion-based recommended task section
- 📆 Calendar filtering and due date support
- 📧 Reminder emails with styled welcome email
- 📱 SMS reminders with Twilio or mock fallback
- 🧾 File + database activity logging
- 🛡️ Rate limiting, CORS handling, session support, and admin-protected cleanup endpoint

## 🧠 Emotion-Aware Design

Emotion analysis in this project is:

- optional, not forced
- assistive, not diagnostic
- used only to suggest better task ordering
- easy to dismiss if the user wants manual control only

Current normalized emotion outcomes:

- 🎯 `focused`
- 😣 `stressed`
- 😐 `neutral`

DeepFace is used when available. If camera analysis fails, the app safely falls back to a neutral response so the workflow keeps working.

## 🏗️ Project Architecture

```text
Task Prioritization System Using Emotion Analysis/
|
|-- Frontend/
|   |-- index.html
|   |-- login.html
|   |-- signup.html
|   |-- forgot-password.html
|   |-- dashboard.html
|   |-- dashboard-script.js
|   |-- dashboard-style.css
|   |-- about.html / contact.html / privacy.html / terms.html
|   `-- config.js
|
|-- Backend/
|   |-- app.py
|   |-- database.py
|   |-- models.py
|   |-- task_routes.py
|   |-- log_routes.py
|   |-- notifications.py
|   |-- reminder_service.py
|   |-- google_oauth.py
|   |-- activity_logger.py
|   |-- migrate_sqlite_to_postgres.py
|   |-- query_db.py
|   |-- reset_config.py
|   |-- requirements.txt
|   `-- modules/
|       |-- emotion.py
|       `-- task.py
|
|-- API/
|   `-- routes.py
|
|-- Data_Storage/
|-- .env.example
|-- start.bat
`-- README.md
```

## 🛠️ Tech Stack

### Frontend

- HTML5
- CSS3
- Vanilla JavaScript

### Backend

- Flask
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-CORS
- Flask-Limiter
- Flask-Session
- APScheduler

### Database

- PostgreSQL for deployment / production use
- SQLite local fallback during development

### AI / Imaging

- DeepFace
- TensorFlow
- NumPy
- Pillow

### Notifications & Integrations

- SMTP email
- Twilio SMS
- Google OAuth
- Gmail API helpers

## 🔄 How The System Works

### 1. User authentication

- User signs up with email, password, optional phone, and notification preference.
- Login returns `access_token` and `refresh_token`.
- Protected routes use `Authorization: Bearer <token>`.
- If access token expires, the frontend refreshes it automatically.

### 2. Task creation and prioritization

- User adds a task from the dashboard.
- Task can include importance, urgency, due date, due time, reminder time, and reminder method.
- The dashboard can organize tasks using:
  - Eisenhower Matrix
  - Impact vs Effort
  - MoSCoW

### 3. Emotion scan

- User explicitly clicks `Scan Me`.
- Camera opens for a one-time 5-second scan.
- Image is analyzed and mapped to one of the app emotion states.
- App suggests a better task order and shows recommended tasks.

### 4. Reminder delivery

- User can choose email, SMS, or both as preferred notification style.
- Due reminders can be dispatched for the authenticated user.
- The app can send reminder emails and test SMS messages.

### 5. Logging and audit trail

- Important actions are stored in:
  - `Backend/logs.txt`
  - `user_activity_logs` database table

## 🖥️ Frontend Pages

- 🏠 `index.html` - landing page
- 🔑 `login.html` - login form
- 🆕 `signup.html` - registration form
- 🔁 `forgot-password.html` - password reset flow
- 📊 `dashboard.html` - main productivity dashboard
- ℹ️ `about.html` - project introduction
- 📞 `contact.html` - contact page
- 🔒 `privacy.html` - privacy page
- 📜 `terms.html` - terms page

## 📊 Dashboard Features

- Quick add task input
- Due date and due time input
- Task count and filtered views
- Left sidebar for lists and filters
- Right sidebar for notification settings and Gmail connection
- Mini calendar with date filtering
- Theme toggle
- Emotion result modal
- Recommended-for-you section
- Profile notification settings with phone country selection

## 🗃️ Data Models

### `User`

- full name
- email
- password hash
- phone
- notification preference
- Gmail connection details
- welcome / nudge timestamps

### `Task`

- title
- importance
- urgency
- completed status
- emotion applied
- due date and due time
- reminder timestamp
- reminder method
- reminder phone
- reminder delivery state

### `EmotionLog`

- user id
- emotion
- confidence
- scanned time

### `UserActivityLog`

- user email
- action
- details
- timestamp

## 🔐 API Overview

### Auth routes

- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `GET /api/auth/profile`
- `PUT /api/auth/profile`
- `POST /api/auth/forgot-password`
- `POST /api/auth/verify-reset-code`
- `POST /api/auth/reset-password`
- `POST /api/auth/sms/test`
- `GET /api/auth/google-mail/status`
- `POST /api/auth/google-mail/start`
- `GET /api/auth/google-mail/callback`
- `POST /api/auth/google-mail/disconnect`

### Task routes

- `GET /api/tasks`
- `POST /api/tasks`
- `PUT /api/tasks/<id>`
- `DELETE /api/tasks/<id>`
- `PATCH /api/tasks/<id>/complete`
- `POST /api/tasks/emotion/log`
- `POST /api/tasks/emotion-scan`
- `POST /api/tasks/reminders/dispatch`
- `POST /api/tasks/reminders/debug`
- `GET /api/tasks/verify-ownership`
- `POST /api/tasks/fix-user-mapping`

### Log routes

- `GET /api/logs`

## 🔒 Security Notes

- JWT protects profile, task, reminder, and log routes.
- Rate limiting is enabled using `Flask-Limiter`.
- CORS is configured for localhost and Vercel-style frontend origins.
- Sensitive cleanup endpoint `/api/tasks/fix-user-mapping` requires:
  - valid JWT
  - `X-ADMIN-KEY` header matching `ADMIN_SECRET_KEY`

## ⚙️ Environment Variables

Use `.env.example` as your template.

Important configuration groups include:

- `SECRET_KEY`, `JWT_SECRET_KEY`, `ADMIN_SECRET_KEY`
- `JWT_ACCESS_EXPIRES_SECONDS`, `JWT_REFRESH_EXPIRES_SECONDS`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `RATELIMIT_STORAGE_URI`
- `EMAIL_PROVIDER`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`
- `SMS_PROVIDER`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_OAUTH_REDIRECT_URI`
- `REMINDER_DAILY_HOUR_UTC`

## 🚀 Local Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r Backend/requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env
```

Then update `.env` with your real values.

### 5. Start the backend

```bash
python Backend/app.py
```

### 6. Open the app

```text
http://localhost:5000/
```

### 7. Optional shortcut

You can also start the app with:

```bash
start.bat
```

This script starts the Flask server and opens the browser automatically.

## 🗄️ Database Behavior

- If `DATABASE_URL` is set, the app uses PostgreSQL.
- If not, the app falls back to local SQLite using `sqlite:///local.db`.
- Tables are created automatically at startup.
- The app also performs lightweight column-creation checks on startup for existing databases.

## 📬 Notifications

### Email

- SMTP-based sending is implemented.
- Welcome email is triggered after login.
- Reminder emails are sent for due tasks.

### SMS

- Twilio is supported.
- If Twilio config is missing, the app can fall back to mock SMS logging behavior.
- Phone numbers are normalized into E.164 format.

### Gmail

- Google OAuth flow is available.
- Gmail connection status can be checked from the dashboard.
- Users can connect or disconnect Gmail sender support.

## 🧪 Current Workflow Example

```text
Signup/Login
    ↓
Open Dashboard
    ↓
Create Tasks
    ↓
Set Matrix + Deadlines + Reminder Method
    ↓
Optional Emotion Scan
    ↓
Get Recommended Tasks
    ↓
Receive Reminder Email/SMS
    ↓
Complete Tasks and Track Progress
```

## 📁 Important Files To Know

- `Backend/app.py` - app startup, config, JWT, CORS, DB init, static frontend serving
- `API/routes.py` - auth, profile, password reset, Google mail, SMS test
- `Backend/task_routes.py` - task CRUD, emotion scan, reminders, admin cleanup
- `Backend/models.py` - SQLAlchemy models
- `Backend/modules/emotion.py` - emotion analysis and fallback mapping
- `Backend/reminder_service.py` - reminder and welcome email logic
- `Backend/notifications.py` - email/SMS helpers
- `Backend/log_routes.py` - log viewing API
- `Frontend/dashboard.html` - main dashboard UI
- `Frontend/dashboard-script.js` - frontend app logic

## 🎓 Best Use Cases

- student task planning
- assignment scheduling
- personal productivity
- deadline tracking
- experiment/demo project for AI + productivity integration

## 🔮 Future Improvements

- 🤖 richer ML-based task recommendation engine
- 📈 analytics dashboard for productivity patterns
- 👥 role-based access control
- 🔔 real background scheduler / queue workers for reminders
- 📱 mobile-friendly app shell or PWA support
- 🧩 subtasks, labels, recurring reminders, and attachments
- 🧪 automated tests for APIs and frontend flows

## 📝 Notes

- Emotion analysis is a productivity support feature, not a medical or mental health tool.
- Raw camera image is not stored in the database by current backend logic.
- The frontend and backend are served together by Flask in local mode.
- Some UI text and filters are optimized for demo/project presentation and student use cases.

## 🙌 Summary

This project is more than a basic to-do list. It combines:

- task management 📋
- prioritization strategy 📐
- optional emotion-aware assistance 🧠
- reminders and notifications ⏰
- secure authentication 🔐
- activity tracking 🧾

It is a strong full-stack academic/project portfolio app that shows how productivity systems and assistive AI ideas can work together in a practical way.
