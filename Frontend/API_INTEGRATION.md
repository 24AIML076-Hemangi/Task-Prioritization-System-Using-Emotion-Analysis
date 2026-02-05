# Frontend API Integration Guide

## ✅ Changes Made

Your `dashboard-script.js` now uses the Flask backend API instead of `localStorage`.

### Key Changes:

1. **API Endpoint**: `http://localhost:5000/api/tasks`
2. **User ID Tracking**: Uses `localStorage.userName` to identify user
3. **Task CRUD Operations**:
   - `GET /api/tasks?user_id=username` → Load all tasks for user
   - `POST /api/tasks` → Create new task
   - `PUT /api/tasks/{id}` → Update task (importance, urgency, etc.)
   - `DELETE /api/tasks/{id}` → Delete task
   - `PATCH /api/tasks/{id}/complete` → Toggle completion status

4. **API Field Mapping**:
   - Local: `task.text` → API: `task.title`
   - Local: `task.createdAt` → API: `task.created_at`
   - All other fields match: `id`, `importance`, `urgency`, `completed`

---

## 🚀 How to Test

### Step 1: Start Flask Backend
```bash
cd "d:\Task Prioritization System Using Emotion Analysis"
python Backend/app.py
```
Keep it running! (Should show: `Running on http://localhost:5000`)

### Step 2: Open Frontend in Browser
```
File → Open
Navigate to: d:\Task Prioritization System Using Emotion Analysis\Frontend\login.html
```

### Step 3: Test the Flow
1. **Login**: 
   - Email: `john_doe` (any value)
   - Password: `password123` (any ≥6 chars)
   - Click "Sign in"

2. **Add Task**:
   - Type: "Buy groceries"
   - Press Enter
   - Verify it appears in the list AND in database

3. **Check Database**:
   - Open `Backend/tasks.db` with SQLite viewer
   - Look in `tasks` table
   - Should see your task with:
     - `user_id = 'john_doe'`
     - `title = 'Buy groceries'`
     - `importance = 'not-important'`
     - `urgency = 'not-urgent'`

4. **Update Priority**:
   - Click dropdown next to task
   - Change to "Important"
   - Refresh browser
   - Task should still show "Important" (persisted in DB!)

5. **Delete Task**:
   - Click the trash icon
   - Confirm deletion
   - Task deleted from both UI and database

---

## 🔍 Debugging Tips

### Open Browser Console
Press `F12` and check Console tab for logs:

```
Logged in user: john_doe
Fetching tasks for user: john_doe
Tasks loaded from API: 5 tasks
Task created in API: {id: 1, title: "Buy groceries", ...}
Task updated in API: {id: 1, importance: "important", ...}
```

### If Tasks Don't Load
1. Check that Flask server is running (`Running on http://localhost:5000`)
2. Check browser console for CORS errors
3. Ensure `Backend/tasks.db` exists and has data

### If Tasks Load But Don't Save
1. Check Flask console for error messages
2. Verify database file has write permissions
3. Check network tab in DevTools (F12) for failed requests

---

## 📝 Testing Commands (PowerShell)

While Flask is running, test API directly:

```bash
# Get all tasks for user
curl http://localhost:5000/api/tasks?user_id=john_doe

# Create task
curl -X POST http://localhost:5000/api/tasks `
  -H "Content-Type: application/json" `
  -d '{
    "user_id":"john_doe",
    "title":"Call mom",
    "importance":"important",
    "urgency":"urgent"
  }'

# Get task ID from response, then update it
curl -X PUT http://localhost:5000/api/tasks/1 `
  -H "Content-Type: application/json" `
  -d '{"importance":"not-important"}'

# Delete task
curl -X DELETE http://localhost:5000/api/tasks/1
```

---

## ✨ What's Still Using localStorage

- **Session**: `isLoggedIn`, `userName` (set by login page)
- **Emotion State**: Current emotion (in-memory only, not persisted yet)

All **task data** is now in SQLite database! 🎉

---

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| "Cannot fetch tasks" | Flask server not running. Start with `python Backend/app.py` |
| CORS error | Flask must run on `localhost:5000`. Check app.py has `CORS(app)` |
| Tasks disappear on refresh | Database uninitialized. Delete `tasks.db` and restart Flask |
| Dropdowns don't update | Check browser console for API errors |

---

## Next Steps

1. Add login/user registration to backend
2. Add authentication token (JWT)
3. Add emotion scanning endpoint
4. Add task filters by status/priority
5. Add dark mode support

Enjoy your API-connected dashboard! 🚀
