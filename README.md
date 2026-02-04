# Task Prioritization System Using Emotion Analysis

A lightweight college project that helps users prioritize tasks using a combination of the Eisenhower matrix (Important/Urgent quadrants) and emotion analysis to improve focus and scheduling.

**Frontend inspiration:** The UI is inspired by TickTick — clean, task-focused, and mobile-friendly. Tasks are organized into four quadrants: Important & Urgent, Important & Not Urgent, Not Important & Urgent, Not Important & Not Urgent.

Key features
- Task organization by priority quadrants (urgent/important)
- Emotion analysis module to tag or influence task priority
- Responsive frontend with sign-up / login and a "Forgot Password" flow

Project structure (high level)
- `Frontend/` : HTML, CSS, and JS for the UI (login, signup, forgot-password, main UI)
- `Backend/`  : Flask app and backend modules (task management, emotion analysis)
- `API/`      : API routes for authentication and password reset
- `Data_Storage/` : sample data and storage notes

Quick start (development)
1. Create and activate a Python virtual environment.
2. Install dependencies:
```bash
pip install -r Backend/requirements.txt
```
3. Run the Flask backend (example):
```bash
cd Backend
python app.py
```
4. Open frontend pages in your browser (e.g., `Frontend/login.html`).

Notes
- The password-reset flow currently prints reset codes to the backend console for development; configure SMTP in `Backend/reset_config.py` for real emails.
- Emotion analysis is implemented in `Backend/modules/emotion.py` and can be adapted to your dataset.

