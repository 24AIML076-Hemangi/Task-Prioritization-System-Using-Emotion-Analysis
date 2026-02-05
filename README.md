📌 Smart Task Management Dashboard

(TickTick-Inspired | AI-Assisted Prioritization)

🧠 A modern task management web application that combines manual priority control with AI-assisted emotion-based task reordering, designed ethically and practically for real-world productivity.

**With SQLite Backend**: Tasks now persist in a relational database via a Flask REST API, providing real persistence and user isolation.

🚀 Project Overview

This project is a TickTick-inspired task management dashboard built using:

**Frontend**: HTML, CSS, Vanilla JavaScript (clean, minimal UI)  
**Backend**: Flask + SQLAlchemy + SQLite (data persistence)  
**Communication**: REST API with JSON payloads

Core focus:
- Clean & minimal TickTick-inspired UI ✨
- User-controlled task prioritization 🧩
- Optional AI emotion scan for productivity assistance 🤖
- Ethical, consent-based design 🔐
- **Real data persistence with SQLite** 💾

⚠️ This system does NOT diagnose emotions.
It only assists task ordering when workload becomes overwhelming.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9+
- Git
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Backend Setup

1. **Install Python dependencies**:
```bash
cd Backend
pip install -r requirements.txt
```

2. **Run Flask server**:
```bash
cd ..  # Go to project root
python Backend/app.py
```

You should see:
```
✓ Database initialized successfully!
 * Running on http://localhost:5000
```

### Frontend Setup

1. **Open login page**:
   - File → Open: `Frontend/login.html`
   - Or use a local server: `python -m http.server 8000` in Frontend folder

2. **Login**:
   - Email/Username: `john_doe` (any value)
   - Password: `password123` (any ≥6 chars)
   - Click "Sign in"

3. **Dashboard loads**:
   - Tasks sync with SQLite database
   - Add/update/delete tasks in real-time
   - Changes persist across page refreshes

---

## 🎯 Key Features
✅ User Authentication

Login page (index.html)

Successful login redirects to dashboard (dashboard.html)

📝 Task Management

Add tasks easily

Mark tasks as completed

Clean checkbox-based UI (TickTick-style)

📊 Manual Priority System (User First)

Each task has two dropdowns:

Importance

Important

Not Important

Urgency

Urgent

Not Urgent

Tasks are classified using the Eisenhower Matrix:

Priority Order	Category
🔴 1	Important + Urgent
🟠 2	Important + Not Urgent
🟡 3	Not Important + Urgent
🟢 4	Not Important + Not Urgent

👉 Important tasks always stay at the top.
👉 Manual priority is never overridden by AI.

🧠 AI-Assisted Emotion Scan (Optional)

🎥 A floating camera button appears only when:

Important tasks > 5

OR all important tasks are pending

How it works:

User clicks emotion scan button

Browser asks for webcam permission

One frame is captured

Image is sent to backend (/emotion-scan)

Backend returns:

{
  "emotion": "focused | stressed | neutral",
  "confidence": 0.8
}

🧩 Emotion scan is used ONLY to reorder tasks
within the same priority group.

Examples:

😵 Stressed → easier important tasks first

🎯 Focused → high-effort important tasks first

⚠️ Important tasks always remain top priority

🎨 UI & UX Design

Inspired by TickTick Web App (not cloned):

Light background (#f7f8fa)

White task cards with rounded corners 🤍

Subtle shadows & spacing

Modern sans-serif fonts

Floating action button 🎥

Smooth hover & transition effects

Clean, distraction-free layout

🛡️ Ethics & Privacy Considerations

✔️ Explicit user consent for webcam access
✔️ Emotion scan is optional
✔️ No continuous monitoring
✔️ No mental health diagnosis
✔️ Data used only for task prioritization

🧠 AI is an assistant, not an authority.

🛠️ Tech Stack

**Frontend**: 
- HTML 5, CSS 3
- Vanilla JavaScript (ES6+)
- Fetch API for HTTP requests

**Backend**: 
- Flask 2.3
- SQLAlchemy ORM
- SQLite3 Database

**Communication**:
- REST API with JSON payloads
- CORS enabled for frontend requests
- Async/await for non-blocking operations

**No heavy frameworks**:
- No React, Vue, or Angular
- No heavy ML libraries (mock emotion fallback)
- Keep it simple, transparent, maintainable

📂 Folder Structure
```
.
├── Frontend/
│   ├── login.html                 # Login page
│   ├── login-style.css            # Login styles
│   ├── login-script.js            # Login logic
│   ├── dashboard.html             # Task dashboard
│   ├── dashboard-style.css        # Dashboard styles
│   ├── dashboard-script.js        # Dashboard + API client
│   ├── UI_GUIDE.md                # UI documentation
│   └── API_INTEGRATION.md         # API usage guide
│
├── Backend/
│   ├── app.py                     # Flask app entry point
│   ├── database.py                # SQLAlchemy initialization
│   ├── models.py                  # Task & EmotionLog models
│   ├── task_routes.py             # REST API endpoints
│   ├── requirements.txt           # Python dependencies
│   ├── tasks.db                   # SQLite database (auto-created)
│   └── modules/
│       ├── emotion.py             # Emotion detection
│       └── task.py                # Task logic
│
├── API/
│   ├── __init__.py
│   └── routes.py                  # Authentication routes
│
├── Data_Storage/
│   └── sample_data.csv            # Sample task data
│
├── README.md                       # This file
├── FORGOT_PASSWORD_SETUP.md       # Password reset setup
└── INTEGRATION_STATUS.md          # Backend-frontend integration status
```
🧪 Development Notes

**Database**: 
- SQLite at `Backend/tasks.db` (auto-created)
- Proper schema with timestamps
- User isolation via `user_id` field

**API**:
- Mock emotion response if backend unavailable
- Full CRUD operations for tasks
- Proper error handling & logging

**Testing**:
- Use browser console (F12) for API logs
- Use SQLite viewer to inspect database
- Test with curl commands (see API_INTEGRATION.md)

**Production Considerations**:
- Use PostgreSQL instead of SQLite
- Add JWT authentication
- Implement rate limiting
- Add input validation & sanitization
- Use HTTPS only

🏁 Conclusion

This project demonstrates:

✅ Strong frontend fundamentals

✅ Intelligent task prioritization

✅ Ethical AI usage

✅ Real-world productivity thinking

A practical, placement-ready task management system. 💪🔥