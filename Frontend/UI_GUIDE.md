# Focus Task Dashboard — UI Guide

## Overview
A clean, TickTick-inspired task management interface with emotion-aware task prioritization.

---

## 1. Login Page (`login.html`)

### Layout
- **Header Bar**: Brand "Focus" with logo circle (✓) in gradient purple
- **Two-Column Card**:
  - **Left**: Sign-in form (Email/username, Password, Sign in button, Create account link, Footer text)
  - **Right**: Welcome message and info about the demo (emotion-based reprioritization, local camera access)

### Styling
- Light background (`#f7f8fa`)
- White card with subtle shadow
- System fonts (SF Pro, Segoe UI)
- Gradient buttons (purple `#667eea` → `#764ba2`)
- Smooth transitions and hover effects
- Responsive on mobile (card becomes single column)

### Flow
1. User enters email/username and password
2. Clicks "Sign in" or "Create account"
3. Script validates (non-empty, password ≥6 chars)
4. Sets `localStorage` flags (`isLoggedIn=true`, `userName`)
5. Redirects to `dashboard.html`

---

## 2. Dashboard (`dashboard.html`)

### Layout
- **Header**: Brand logo, "Today" title, User name, Logout button
- **Add Task Section**: Input field + button; Emotion badge (when active)
- **Tasks Container**: "My Tasks" header with count; Task list (empty state or tasks)
- **FAB (Floating Action Button)**: Camera icon, bottom-right; visible only per visibility rules

### Task Card Structure
Each task includes:
- **Checkbox**: Mark task as done
- **Task Text**: Full task description
- **Importance Dropdown**: "Important" / "Not Important"
- **Urgency Dropdown**: "Urgent" / "Not Urgent"
- **Delete Button**: Remove task

### Emotion Badge
Appears after emotion scan; shows:
- Emotion icon (😟 stressed, 😊 focused, 😐 neutral)
- Emotion label + confidence (e.g., "focused 87%")
- Clear button (×)

---

## 3. Eisenhower Matrix Ordering

Tasks are automatically grouped and sorted by:

1. **Important + Urgent** (highest priority)
2. **Important + Not Urgent**
3. **Not Important + Urgent**
4. **Not Important + Not Urgent** (lowest priority)

Within each group:
- **If emotion is "stressed"**: Easier tasks (by text length) appear first
- **If emotion is "focused"**: Harder tasks appear first
- **Otherwise**: Stable original order

---

## 4. Emotion-Scan FAB Visibility Rules

The camera button is **visible only** when:
- Number of Important tasks **> 5**, OR
- Number of Important tasks **> 0** AND all Important tasks are **pending** (not completed)

Otherwise, the button is hidden.

---

## 5. Camera Modal

### Modal Components
- **Header**: "Scan Your Emotion" title + close button (×)
- **Video Feed**: Live webcam stream
- **Status Message**: Permission requests or "Ready to scan"
- **Capture Button**: Capture single frame
- **Cancel Button**: Close without scanning

### Permission Flow
1. User clicks FAB
2. Browser requests camera permission
3. If granted: Video stream starts
4. User clicks "Capture"
5. Frame sent to `/emotion-scan` endpoint (or mock)
6. Result modal displays detected emotion

---

## 6. Result Modal

After emotion scan:
- Shows detected emotion (icon + label + confidence)
- Auto-hides button after 3 seconds or manual close
- Tasks **within the same priority group** are reordered based on emotion
- Important tasks always stay above non-important ones

---

## 7. Color & Typography

### Colors
- **Background**: `#f7f8fa` (light gray)
- **Card/Surface**: `#ffffff` (white)
- **Primary**: `#667eea` → `#764ba2` (gradient)
- **Accent**: `#5b21b6` (purple for brand)
- **Text**: `#2d3748` (dark), `#6b7280` (muted)
- **Borders**: `#e6eef6` (subtle blue-gray)

### Fonts
- **System Stack**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, ...`
- **Sizes**: 13px (small), 14px (body), 15px (input), 20px (title)
- **Weights**: 500 (normal), 600 (semi-bold), 700 (bold)

---

## 8. Key Features

✅ **Responsive Design**: Works on desktop, tablet, mobile  
✅ **Local Storage**: Tasks and session persist across refreshes  
✅ **Emotion Integration**: Optional, non-invasive emotion-based reordering  
✅ **Accessibility**: Semantic HTML, clear labels, keyboard navigation  
✅ **Performance**: Vanilla JS, no external dependencies (except camera API)  

---

## 9. File Structure

```
Frontend/
├── login.html             # Login page
├── login-style.css        # Login styles
├── login-script.js        # Login logic & redirect
├── dashboard.html         # Dashboard page
├── dashboard-style.css    # Dashboard styles & layout
├── dashboard-script.js    # Task management & emotion logic
├── UI_GUIDE.md            # This file
```

---

## 10. Testing the UI

1. **Start with login.html**: Sign in with any username/password (≥6 chars)
2. **Redirects to dashboard.html**: Should see empty state
3. **Add tasks**: Type in the input, press Enter or click +
4. **Adjust priority**: Use dropdowns to set Importance/Urgency
5. **Emotion scan**: Click FAB when visible (≥1 Important task), allow camera, capture
6. **Watch reordering**: Tasks within same group shuffle based on emotion

---

## 11. Browser Requirements

- **Camera API**: WebRTC (most modern browsers)
- **localStorage**: For session & task persistence
- **Fetch API**: For emotion-scan endpoint
- **Canvas**: For frame capture from video stream
- **CSS Grid/Flexbox**: For layout

**Tested on**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

---

*Last updated: 2025. Built with vanilla HTML/CSS/JS for maximum simplicity and transparency.*
