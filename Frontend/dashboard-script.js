/* ============================================
   TaskPrioritize - Minimal Script
   Clean, Functional Task Management
   ============================================ */

class TaskManager {
    constructor() {
        this.tasks = [];
        this.userId = null;
        this.apiUrl = 'http://localhost:5000/api/tasks';
        this.authApiUrl = 'http://localhost:5000/api/auth';
        this.currentEmotion = null;
        this.cameraStream = null;
        this.calendarMonth = new Date().getMonth();
        this.calendarYear = new Date().getFullYear();
        this.selectedDate = null;
        this.activeFilter = 'today';
        this.taskLists = this.loadTaskLists();
        this.selectedTaskId = null;
        this.userProfile = null;
        this.scanTimerId = null;
        this.scanIntervalId = null;
        this.pendingEmotionResult = null;
        this.emotionScanEnabled = false;

        this.init();
    }

    async init() {
        // Check login
        if (!localStorage.getItem('isLoggedIn')) {
            window.location.href = 'login.html';
            return;
        }

        // Use email as user_id for API calls (unique identifier)
        this.userId = localStorage.getItem('userEmail') || localStorage.getItem('userName') || 'User';
        const userName = localStorage.getItem('userName') || 'User';
        document.getElementById('userInfo').textContent = userName;

        await this.loadUserProfile();
        await this.loadTasks();
        this.setupEventListeners();
        this.generateCalendar();
        this.renderTasks();
        this.startReminderLoop();
        this.startAutoRefresh();
    }

    /* ============================================
       DATA - Load & Save
       ============================================ */

    async loadTasks() {
        try {
            const response = await fetch(`${this.apiUrl}?user_id=${this.userId}`);
            if (response.ok) {
                this.tasks = await response.json();
            } else {
                this.tasks = [];
            }
        } catch (error) {
            console.error('Load error:', error);
            this.tasks = [];
        }
    }

    async createTask(title, dueAtLocal = null) {
        try {
            const payload = {
                user_id: this.userId,
                title: title.trim(),
                importance: 'not-important',
                urgency: 'not-urgent',
                due_at: dueAtLocal,
            };
            
            console.log('📝 Creating task:', payload);
            
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                const task = await response.json();
                this.setTaskList(task.id, 'inbox');
                console.log('✅ Task created:', task);
                return task;
            } else {
                const error = await response.json();
                console.error('❌ Task creation failed:', error);
            }
        } catch (error) {
            console.error('Create error:', error);
        }
        return null;
    }

    async deleteTask(id) {
        try {
            await fetch(`${this.apiUrl}/${id}`, { method: 'DELETE' });
            this.tasks = this.tasks.filter(t => t.id !== id);
            if (this.taskLists[id]) {
                delete this.taskLists[id];
                this.saveTaskLists();
            }
            this.renderTasks();
            this.generateCalendar();
        } catch (error) {
            console.error('Delete error:', error);
        }
    }

    async loadUserProfile() {
        try {
            const response = await fetch(`${this.authApiUrl}/profile?email=${encodeURIComponent(this.userId)}`);
            if (!response.ok) return;
            this.userProfile = await response.json();
            this.populateProfileForm();
        } catch (error) {
            console.error('Profile load error:', error);
        }
    }

    populateProfileForm() {
        const methodEl = document.getElementById('profileNotificationMethod');
        const phoneEl = document.getElementById('profilePhone');
        if (!methodEl || !phoneEl || !this.userProfile) return;

        methodEl.value = this.userProfile.notification_preference || 'email';
        phoneEl.value = this.userProfile.phone || '';
    }

    async saveUserProfile() {
        const methodEl = document.getElementById('profileNotificationMethod');
        const phoneEl = document.getElementById('profilePhone');
        if (!methodEl || !phoneEl) return;

        const payload = {
            email: this.userId,
            notification_preference: methodEl.value || 'email',
            phone: phoneEl.value.trim() || null,
        };

        try {
            const response = await fetch(`${this.authApiUrl}/profile`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || 'Failed to save profile settings');
                return;
            }
            this.userProfile = data;
            alert('Notification settings saved');
        } catch (error) {
            console.error('Profile save error:', error);
            alert('Unable to save notification settings');
        }
    }

    async toggleTask(id) {
        try {
            const response = await fetch(`${this.apiUrl}/${id}/complete`, {
                method: 'PATCH',
            });
            if (response.ok) {
                const updated = await response.json();
                const task = this.tasks.find(t => t.id === id);
                if (task) task.completed = updated.completed;
                this.renderTasks();
            }
        } catch (error) {
            console.error('Toggle error:', error);
        }
    }

    /* ============================================
       UI - Render
       ============================================ */

    renderTasks() {
        const list = document.getElementById('tasksList');
        const count = document.getElementById('taskCount');

        let filtered = this.applyFilter(this.tasks);

        // Filter by selected date if any
        if (this.selectedDate) {
            filtered = filtered.filter(t => {
                const d = this.getTaskReferenceDate(t);
                if (!d) return false;
                return this.getLocalDateKey(d) === this.selectedDate;
            });
        }

        filtered = this.sortTasksForDisplay(filtered);

        // Separate completed and active
        const active = filtered.filter(t => !t.completed);
        const completed = filtered.filter(t => t.completed);

        console.log(`📊 Rendering tasks: ${active.length} active, ${completed.length} completed`);
        count.textContent = `${active.length} tasks`;

        if (active.length === 0 && completed.length === 0) {
            list.innerHTML = '<div class="empty-state"><p>📋 No tasks. Add one to get started!</p></div>';
            return;
        }

        let html = '';

        // Active first
        active.forEach(task => {
            html += this.renderTaskItem(task);
        });

        // Completed after
        if (completed.length > 0) {
            html += '<div style="opacity:0.5">';
            completed.forEach(task => {
                html += this.renderTaskItem(task);
            });
            html += '</div>';
        }

        console.log('🎨 HTML to render:', html.substring(0, 200) + '...');
        list.innerHTML = html;
        this.attachListeners();
    }

    renderTaskItem(task) {
        const text = task.title || task.text;
        const matrix = this.getMatrixClass(task);
        const checked = task.completed ? 'checked' : '';
        const list = this.getTaskList(task.id);
        const dueMeta = this.formatDueMeta(task);

        return `
            <div class="task-item ${task.completed ? 'completed' : ''} ${matrix}" data-id="${task.id}">
                <input type="checkbox" class="task-checkbox" ${checked} />
                <div class="task-main">
                    <span class="task-name">${this.escape(text)}</span>
                    ${dueMeta ? `<span class="task-meta ${dueMeta.overdue ? 'overdue' : ''}">${this.escape(dueMeta.label)}</span>` : ''}
                </div>
                
                <div class="task-controls">
                    <select class="task-list" data-id="${task.id}" title="Set list">
                        <option value="inbox" ${list === 'inbox' ? 'selected' : ''}>Inbox</option>
                        <option value="work" ${list === 'work' ? 'selected' : ''}>Work</option>
                        <option value="study" ${list === 'study' ? 'selected' : ''}>Study</option>
                        <option value="personal" ${list === 'personal' ? 'selected' : ''}>Personal</option>
                    </select>

                    <select class="task-importance" data-id="${task.id}" title="Set importance">
                        <option value="important" ${task.importance === 'important' ? 'selected' : ''}>⭐ Important</option>
                        <option value="not-important" ${task.importance === 'not-important' ? 'selected' : ''}>☆ Not Important</option>
                    </select>
                    
                    <select class="task-urgency" data-id="${task.id}" title="Set urgency">
                        <option value="urgent" ${task.urgency === 'urgent' ? 'selected' : ''}>🚨 Urgent</option>
                        <option value="not-urgent" ${task.urgency === 'not-urgent' ? 'selected' : ''}>◯ Not Urgent</option>
                    </select>
                </div>
                
                <div class="task-actions">
                    <button class="task-delete" data-id="${task.id}" title="Delete">
                        ✕
                    </button>
                </div>
            </div>
        `;
    }

    getMatrixClass(task) {
        const imp = task.importance === 'important';
        const urg = task.urgency === 'urgent';
        if (imp && urg) return 'imp-urg';
        if (imp && !urg) return 'imp-nurg';
        if (!imp && urg) return 'nimp-urg';
        return 'nimp-nurg';
    }

    getTaskReferenceDate(task) {
        const dateValue = task.due_at || task.created_at || task.createdAt;
        if (!dateValue) return null;
        const d = new Date(dateValue);
        return Number.isNaN(d.getTime()) ? null : d;
    }

    getLocalDateKey(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    formatDueMeta(task) {
        if (!task.due_at) return null;
        const due = new Date(task.due_at);
        if (Number.isNaN(due.getTime())) return null;

        const formatted = due.toLocaleString([], {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        });

        return {
            label: `Deadline: ${formatted}`,
            overdue: !task.completed && due.getTime() < Date.now(),
        };
    }

    attachListeners() {
        // Checkboxes
        document.querySelectorAll('.task-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const id = parseInt(e.target.closest('.task-item').dataset.id);
                this.toggleTask(id);
            });
        });

        // Importance dropdown
        document.querySelectorAll('.task-importance').forEach(select => {
            select.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                const importance = e.target.value;
                console.log(`⭐ Importance changed for task ${id}: ${importance}`);
                this.updateTaskPriority(id, importance, 'importance');
            });
        });


        // List dropdown
        document.querySelectorAll('.task-list').forEach(select => {
            select.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                const list = e.target.value;
                this.setTaskList(id, list);
                this.renderTasks();
            });
        });

        // Urgency dropdown
        document.querySelectorAll('.task-urgency').forEach(select => {
            select.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                const urgency = e.target.value;
                console.log(`🚨 Urgency changed for task ${id}: ${urgency}`);
                this.updateTaskPriority(id, urgency, 'urgency');
            });
        });

        // Delete buttons
        document.querySelectorAll('.task-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.target.dataset.id);
                if (confirm('Delete this task?')) {
                    this.deleteTask(id);
                }
            });
        });
        
        // Task details panel
        document.querySelectorAll('.task-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (e.target.closest('.task-actions') || e.target.closest('.task-controls') || e.target.classList.contains('task-checkbox')) {
                    return;
                }
                const id = parseInt(item.dataset.id);
                this.selectedTaskId = id;
                const task = this.tasks.find(t => t.id === id);
                if (task) this.renderTaskDetails(task);
            });
        });

        console.log(`📌 Listeners attached: ${document.querySelectorAll('.task-checkbox').length} tasks`);
    }

    async updateTaskPriority(id, value, field) {
        try {
            const task = this.tasks.find(t => t.id === id);
            if (!task) return;

            const updateData = { [field]: value };
            const response = await fetch(`${this.apiUrl}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData),
            });

            if (response.ok) {
                const updated = await response.json();
                Object.assign(task, updated);
                this.renderTasks();
                console.log(`✓ Task ${id} ${field} updated to ${value}`);
            }
        } catch (error) {
            console.error('Priority update error:', error);
        }
    }


    loadTaskLists() {
        try {
            return JSON.parse(localStorage.getItem('taskLists') || '{}');
        } catch {
            return {};
        }
    }

    saveTaskLists() {
        localStorage.setItem('taskLists', JSON.stringify(this.taskLists));
    }

    getTaskList(taskId) {
        return this.taskLists[taskId] || 'inbox';
    }

    setTaskList(taskId, list) {
        this.taskLists[taskId] = list;
        this.saveTaskLists();
    }

    applyFilter(tasks) {
        const now = new Date();
        const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const endOfNext7 = new Date(startOfToday);
        endOfNext7.setDate(endOfNext7.getDate() + 7);

        switch (this.activeFilter) {
            case 'today':
                return tasks.filter(t => {
                    const d = this.getTaskReferenceDate(t);
                    if (!d) return false;
                    return d >= startOfToday && d < new Date(startOfToday.getTime() + 86400000);
                });
            case 'next7days':
                return tasks.filter(t => {
                    const d = this.getTaskReferenceDate(t);
                    if (!d) return false;
                    return d >= startOfToday && d < endOfNext7;
                });
            case 'inbox':
                return tasks.filter(t => this.getTaskList(t.id) === 'inbox');
            case 'list-work':
                return tasks.filter(t => this.getTaskList(t.id) === 'work');
            case 'list-study':
                return tasks.filter(t => this.getTaskList(t.id) === 'study');
            case 'list-personal':
                return tasks.filter(t => this.getTaskList(t.id) === 'personal');
            case 'important':
                return tasks.filter(t => t.importance === 'important' && !t.completed);
            case 'urgent':
                return tasks.filter(t => t.urgency === 'urgent' && !t.completed);
            case 'completed':
                return tasks.filter(t => t.completed);
            default:
                return tasks;
        }
    }

    getMatrixRank(task) {
        const imp = task.importance === 'important';
        const urg = task.urgency === 'urgent';
        if (imp && urg) return 1;
        if (imp && !urg) return 2;
        if (!imp && urg) return 3;
        return 4;
    }

    compareTaskEffort(a, b) {
        const aLen = (a.title || '').trim().length;
        const bLen = (b.title || '').trim().length;

        if (this.currentEmotion === 'stressed') return aLen - bLen;
        if (this.currentEmotion === 'focused') return bLen - aLen;

        const aTime = new Date(a.created_at || 0).getTime();
        const bTime = new Date(b.created_at || 0).getTime();
        return aTime - bTime;
    }

    sortTasksForDisplay(tasks) {
        return [...tasks].sort((a, b) => {
            const rankDiff = this.getMatrixRank(a) - this.getMatrixRank(b);
            if (rankDiff !== 0) return rankDiff;
            return this.compareTaskEffort(a, b);
        });
    }

    renderTaskDetails(task) {
        const panel = document.getElementById('taskDetailsPanel');
        const content = document.getElementById('taskDetailsContent');
        if (!panel || !content) return;

        const due = task.due_at ? new Date(task.due_at) : null;
        const reminder = task.reminder_at ? new Date(task.reminder_at) : null;
        const dueValue = due ? this.toLocalInputValue(due) : '';
        const reminderValue = reminder ? this.toLocalInputValue(reminder) : '';
        const defaultMethod = task.reminder_method || (this.userProfile?.notification_preference || '');
        const defaultPhone = task.reminder_phone || (this.userProfile?.phone || '');

        content.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">Title</div>
                <div class="detail-value">${this.escape(task.title || '')}</div>
            </div>
            <div class="detail-form">
                <label>Due date</label>
                <input type="datetime-local" id="detailDue" value="${dueValue}" />

                <label>Reminder</label>
                <input type="datetime-local" id="detailReminder" value="${reminderValue}" />

                <label>Reminder method</label>
                <select id="detailMethod">
                    <option value="" ${!defaultMethod ? 'selected' : ''}>None</option>
                    <option value="email" ${defaultMethod === 'email' ? 'selected' : ''}>Email</option>
                    <option value="sms" ${defaultMethod === 'sms' ? 'selected' : ''}>SMS</option>
                    <option value="both" ${defaultMethod === 'both' ? 'selected' : ''}>Email + SMS</option>
                </select>

                <label>Phone (for SMS)</label>
                <input type="tel" id="detailPhone" placeholder="+1..." value="${defaultPhone}" />

                <div class="detail-actions">
                    <button class="btn-secondary" id="detailClear">Clear</button>
                    <button class="btn-primary" id="detailSave">Save</button>
                </div>
            </div>
        `;

        panel.style.display = 'block';

        document.getElementById('detailSave').addEventListener('click', () => {
            this.updateTaskDetails(task.id);
        });

        document.getElementById('detailClear').addEventListener('click', () => {
            document.getElementById('detailDue').value = '';
            document.getElementById('detailReminder').value = '';
            document.getElementById('detailMethod').value = '';
            document.getElementById('detailPhone').value = '';
            this.updateTaskDetails(task.id, true);
        });
    }

    async updateTaskDetails(id, clearAll = false) {
        const task = this.tasks.find(t => t.id === id);
        if (!task) return;

        const dueRaw = document.getElementById('detailDue').value;
        const reminderRaw = document.getElementById('detailReminder').value;
        const method = document.getElementById('detailMethod').value;
        const phone = document.getElementById('detailPhone').value.trim();

        const updateData = {
            due_at: dueRaw || null,
            reminder_at: reminderRaw || null,
            reminder_method: method || null,
            reminder_phone: phone || null,
        };

        if (clearAll) {
            updateData.due_at = null;
            updateData.reminder_at = null;
            updateData.reminder_method = null;
            updateData.reminder_phone = null;
        }

        try {
            const response = await fetch(`${this.apiUrl}/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updateData),
            });
            if (response.ok) {
                const updated = await response.json();
                Object.assign(task, updated);
                this.renderTasks();
                this.renderTaskDetails(task);
                this.generateCalendar();
            }
        } catch (error) {
            console.error('Detail update error:', error);
        }
    }

    toLocalInputValue(date) {
        const pad = (n) => String(n).padStart(2, '0');
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    startReminderLoop() {
        const run = async () => {
            try {
                const res = await fetch(`${this.apiUrl}/reminders/dispatch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: this.userId }),
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.sent && data.sent > 0) {
                        console.log(`Reminders sent: ${data.sent}`);
                    }
                }
            } catch (err) {
                console.log('Reminder dispatch failed');
            }
        };

        run();
        setInterval(run, 60000);
    }

    startAutoRefresh() {
        const run = async () => {
            try {
                const before = JSON.stringify(this.tasks);
                await this.loadTasks();
                const after = JSON.stringify(this.tasks);

                if (before !== after) {
                    this.renderTasks();
                    this.generateCalendar();

                    if (this.selectedTaskId) {
                        const selected = this.tasks.find(t => t.id === this.selectedTaskId);
                        if (selected) {
                            this.renderTaskDetails(selected);
                        } else {
                            const panel = document.getElementById('taskDetailsPanel');
                            if (panel) panel.style.display = 'none';
                        }
                    }
                }
            } catch (err) {
                console.log('Auto refresh failed');
            }
        };

        setInterval(run, 5000);
    }

    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /* ============================================
       Calendar
       ============================================ */

    generateCalendar() {
        const container = document.getElementById('miniCalendar');
        const dueDateSet = new Set(
            this.tasks
                .filter(t => t.due_at)
                .map(t => {
                    const d = new Date(t.due_at);
                    if (Number.isNaN(d.getTime())) return null;
                    return this.getLocalDateKey(d);
                })
                .filter(Boolean)
        );

        const firstDay = new Date(this.calendarYear, this.calendarMonth, 1).getDay();
        const lastDate = new Date(this.calendarYear, this.calendarMonth + 1, 0).getDate();
        const monthName = new Date(this.calendarYear, this.calendarMonth).toLocaleString('default', { month: 'long' });

        let html = `<div class="cal-header">${monthName} ${this.calendarYear}</div>`;
        html += '<div class="cal-grid">';

        // Day labels
        ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].forEach(d => {
            html += `<div class="cal-label">${d}</div>`;
        });

        // Blanks
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="cal-day" style="visibility:hidden;"></div>';
        }

        // Days
        for (let d = 1; d <= lastDate; d++) {
            const date = new Date(this.calendarYear, this.calendarMonth, d);
            const dayKey = this.getLocalDateKey(date);
            const isSelected = this.selectedDate === dayKey ? 'selected' : '';
            const hasDeadline = dueDateSet.has(dayKey) ? 'has-deadline' : '';
            html += `<button class="cal-day ${isSelected} ${hasDeadline}" data-date="${dayKey}">${d}</button>`;
        }

        html += '</div>';
        container.innerHTML = html;

        // Attach day click handlers
        container.querySelectorAll('.cal-day[data-date]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const date = e.target.dataset.date;
                this.selectedDate = this.selectedDate === date ? null : date;
                if (this.selectedDate) {
                    this.prefillDueDateFromCalendar(this.selectedDate);
                }
                this.generateCalendar();
                this.renderTasks();
            });
        });
    }

    prefillDueDateFromCalendar(selectedIsoDate) {
        const dueInput = document.getElementById('taskDueInput');
        if (!dueInput) return;

        const existing = dueInput.value ? new Date(dueInput.value) : null;
        const hours = existing && !Number.isNaN(existing.getTime()) ? existing.getHours() : 18;
        const minutes = existing && !Number.isNaN(existing.getTime()) ? existing.getMinutes() : 0;
        const selectedDate = new Date(`${selectedIsoDate}T00:00:00`);
        selectedDate.setHours(hours, minutes, 0, 0);
        dueInput.value = this.toLocalInputValue(selectedDate);
    }

    /* ============================================
       Camera & Emotion
       ============================================ */

    async openCamera() {
        const agreed = await this.ensureEmotionConsent();
        if (!agreed) return;

        const modal = document.getElementById('cameraModal');
        const video = document.getElementById('videoFeed');
        const msg = document.getElementById('cameraMessage');

        modal.classList.add('show');
        document.getElementById('modalOverlay').classList.add('show');
        msg.textContent = 'Accessing camera...';

        try {
            this.cameraStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
            });
            video.srcObject = this.cameraStream;
            await video.play();
            this.startScanCountdown();
        } catch (error) {
            msg.textContent = `Camera error: ${error.message}`;
        }
    }

    stopCamera() {
        if (this.scanTimerId) {
            clearTimeout(this.scanTimerId);
            this.scanTimerId = null;
        }
        if (this.scanIntervalId) {
            clearInterval(this.scanIntervalId);
            this.scanIntervalId = null;
        }
        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach(t => t.stop());
            this.cameraStream = null;
        }
    }

    closeCamera() {
        this.stopCamera();
        document.getElementById('cameraModal').classList.remove('show');
        document.getElementById('modalOverlay').classList.remove('show');
    }

    async analyzeEmotion() {
        const video = document.getElementById('videoFeed');
        const canvas = document.getElementById('captureCanvas');
        const ctx = canvas.getContext('2d');

        if (!video.videoWidth || !video.videoHeight) {
            this.showEmotionResult(this.getMockEmotion());
            return;
        }

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const base64 = canvas.toDataURL('image/jpeg').split(',')[1];

        try {
            // Try real API
            const res = await fetch(`${this.apiUrl}/emotion-scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: base64, user_id: this.userId }),
            });
            if (res.ok) {
                const result = await res.json();
                this.showEmotionResult(result);
                return;
            }
        } catch (err) {
            console.log('API unavailable, using mock');
        }

        // Fallback to mock
        this.showEmotionResult(this.getMockEmotion());
    }

    getMockEmotion() {
        const emotions = [
            { emotion: 'focused', confidence: 0.85 },
            { emotion: 'stressed', confidence: 0.72 },
            { emotion: 'neutral', confidence: 0.88 },
        ];
        return emotions[Math.floor(Math.random() * emotions.length)];
    }

    showEmotionResult(result) {
        this.closeCamera();

        const icons = { focused: '🎯', stressed: '😰', neutral: '😐' };
        const messages = {
            focused: 'You\'re in focus mode! Tackle high-priority tasks.',
            stressed: 'You\'re stressed. Start with easy tasks to build momentum.',
            neutral: 'You\'re neutral. Ready for any task.',
        };

        this.pendingEmotionResult = result;

        document.getElementById('resultIcon').textContent = icons[result.emotion];
        document.getElementById('resultEmotion').textContent = result.emotion;
        document.getElementById('resultConfidence').textContent = Math.round(result.confidence * 100);
        document.getElementById('resultMessage').textContent = messages[result.emotion];

        // Show result modal
        document.getElementById('resultModal').classList.add('show');
        document.getElementById('modalOverlay').classList.add('show');
    }

    applyEmotionToTasks() {
        if (!this.pendingEmotionResult) return;

        this.currentEmotion = this.pendingEmotionResult.emotion;
        const icons = { focused: '🎯', stressed: '😰', neutral: '😐' };
        const badge = document.getElementById('emotionBadge');
        document.getElementById('emotionIcon').textContent = icons[this.currentEmotion] || '😐';
        document.getElementById('emotionLabel').textContent = this.currentEmotion;
        badge.style.display = 'flex';

        this.renderTasks();
        this.closeResult();
    }

    closeResult() {
        this.pendingEmotionResult = null;
        document.getElementById('resultModal').classList.remove('show');
        document.getElementById('modalOverlay').classList.remove('show');
    }

    clearEmotion() {
        this.currentEmotion = null;
        document.getElementById('emotionBadge').style.display = 'none';
        this.renderTasks();
    }

    async ensureEmotionConsent() {
        if (this.emotionScanEnabled) return true;

        const consent = confirm(
            'Emotion scan consent:\n\n1) Camera runs once for 5 seconds only.\n2) One frame is analyzed for task support, not diagnosis.\n3) You can dismiss and keep manual priorities.\n4) Raw camera image is not stored in database.\n\nDo you agree?'
        );

        if (consent) {
            this.emotionScanEnabled = true;
            return true;
        }
        return false;
    }

    startScanCountdown() {
        const msg = document.getElementById('cameraMessage');
        let remaining = 5;
        msg.textContent = `Scanning in ${remaining}s... Keep your face in frame.`;

        this.scanIntervalId = setInterval(() => {
            remaining -= 1;
            if (remaining > 0) {
                msg.textContent = `Scanning in ${remaining}s... Keep your face in frame.`;
            }
        }, 1000);

        this.scanTimerId = setTimeout(() => {
            this.analyzeEmotion();
        }, 5000);
    }

    /* ============================================
       EVENT LISTENERS
       ============================================ */

    setupEventListeners() {
        // Add task
        const input = document.getElementById('taskInput');
        const dueInput = document.getElementById('taskDueInput');
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                const dueAtLocal = dueInput?.value || null;
                const task = await this.createTask(input.value, dueAtLocal);
                if (task) {
                    this.tasks.unshift(task);
                    this.renderTasks();
                    input.value = '';
                    if (dueInput) dueInput.value = '';
                    this.generateCalendar();
                }
            }
        });

        // Toggle calendar (mobile)
        document.getElementById('toggleCalendarBtn')?.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('visible');
        });


        // Sidebar filters
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.activeFilter = btn.dataset.filter;
                const title = btn.textContent.trim();
                document.getElementById('viewTitle').textContent = title || 'Tasks';
                this.renderTasks();
            });
        });

        // Calendar nav
        document.getElementById('prevMonth').addEventListener('click', () => {
            this.calendarMonth--;
            if (this.calendarMonth < 0) {
                this.calendarMonth = 11;
                this.calendarYear--;
            }
            this.generateCalendar();
        });

        document.getElementById('nextMonth').addEventListener('click', () => {
            this.calendarMonth++;
            if (this.calendarMonth > 11) {
                this.calendarMonth = 0;
                this.calendarYear++;
            }
            this.generateCalendar();
        });


        // Clear date filter
        document.getElementById('clearDateFilter').addEventListener('click', () => {
            this.selectedDate = null;
            this.generateCalendar();
            this.renderTasks();
        });

        // Close right panel (mobile)
        document.getElementById('closeRightPanel').addEventListener('click', () => {
            document.getElementById('sidebarRight').classList.remove('visible');
        });

        document.getElementById('saveProfileBtn')?.addEventListener('click', () => {
            this.saveUserProfile();
        });

        // Emotion scan
        document.getElementById('emotionScanBtn').addEventListener('click', () => {
            this.openCamera();
        });

        // Camera controls
        document.getElementById('closeCamera').addEventListener('click', () => this.closeCamera());
        document.getElementById('cancelCamera').addEventListener('click', () => this.closeCamera());
        document.getElementById('captureImage').addEventListener('click', () => this.analyzeEmotion());

        // Result modal
        document.getElementById('closeResult').addEventListener('click', () => this.closeResult());
        document.getElementById('rejectEmotion').addEventListener('click', () => this.closeResult());
        document.getElementById('applyEmotion').addEventListener('click', () => this.applyEmotionToTasks());

        // Emotion badge
        document.getElementById('clearEmotionBtn').addEventListener('click', () => this.clearEmotion());

        // Overlay close
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                const cam = document.getElementById('cameraModal');
                const res = document.getElementById('resultModal');
                if (cam.classList.contains('show')) this.closeCamera();
                else if (res.classList.contains('show')) this.closeResult();
            }
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            if (confirm('Logout?')) {
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userName');
                window.location.href = 'login.html';
            }
        });
    }
}

/* Initialize */
document.addEventListener('DOMContentLoaded', () => {
    new TaskManager();
});


