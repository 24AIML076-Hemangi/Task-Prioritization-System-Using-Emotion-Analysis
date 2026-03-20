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
        this.googleMailStatus = null;
        this.googlePopupPoller = null;
        this.matrixType = this.loadMatrixType();
        this.themeMode = this.loadTheme();
        this.currentEmotionLabel = null;
        this.nextFetchAllowedAt = 0;

        this.init();
    }

    async init() {
        // Check login
        if (!localStorage.getItem('isLoggedIn') || !localStorage.getItem('accessToken')) {
            window.location.href = 'login.html';
            return;
        }

        // Keep email locally for UI display; API identity now comes from JWT
        this.userId = localStorage.getItem('userEmail') || localStorage.getItem('userName') || 'User';
        const userName = localStorage.getItem('userName') || 'User';
        document.getElementById('userInfo').textContent = userName;
        this.applyTheme();

        await this.loadUserProfile();
        await this.loadGoogleMailStatus();
        await this.loadTasks();
        this.setupEventListeners();
        this.generateCalendar();
        this.renderTasks();
        this.startReminderLoop();
        this.startAutoRefresh();
    }

    getAuthHeaders(extra = {}) {
        const token = localStorage.getItem('accessToken');
        const headers = { ...extra };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        return headers;
    }

    async refreshAccessToken() {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) return false;

        const res = await fetch(`${this.authApiUrl}/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${refreshToken}`,
            },
        });

        if (!res.ok) return false;
        const data = await res.json();
        if (!data.access_token) return false;
        localStorage.setItem('accessToken', data.access_token);
        return true;
    }

    async apiFetch(url, options = {}, retried = false) {
        const headers = this.getAuthHeaders(options.headers || {});
        const response = await fetch(url, { ...options, headers });

        if (response.status !== 401 || retried) {
            return response;
        }

        const refreshed = await this.refreshAccessToken();
        if (!refreshed) {
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('userEmail');
            localStorage.removeItem('userName');
            window.location.href = 'login.html';
            return response;
        }

        const retryHeaders = this.getAuthHeaders(options.headers || {});
        return fetch(url, { ...options, headers: retryHeaders });
    }

    loadMatrixType() {
        return localStorage.getItem('matrixType') || 'eisenhower';
    }

    saveMatrixType(type) {
        localStorage.setItem('matrixType', type);
    }

    loadTheme() {
        return localStorage.getItem('themeMode') || 'light';
    }

    applyTheme() {
        const mode = this.themeMode === 'dark' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', mode);
        const label = document.getElementById('themeLabel');
        if (label) {
            label.textContent = mode === 'dark' ? 'Dark' : 'Light';
        }
    }

    toggleTheme() {
        this.themeMode = this.themeMode === 'dark' ? 'light' : 'dark';
        localStorage.setItem('themeMode', this.themeMode);
        this.applyTheme();
    }

    /* ============================================
       DATA - Load & Save
       ============================================ */

    async loadTasks() {
        if (Date.now() < this.nextFetchAllowedAt) {
            return;
        }
        const previousTasks = this.tasks;
        try {
            const response = await this.apiFetch(this.apiUrl);
            if (response.ok) {
                this.tasks = await response.json();
                this.nextFetchAllowedAt = 0;
            } else {
                if (response.status === 429) {
                    // Back off if we hit rate limits.
                    this.nextFetchAllowedAt = Date.now() + 2 * 60 * 1000;
                }
                console.warn(`Task load failed with status ${response.status}; keeping previous task list.`);
                this.tasks = previousTasks;
            }
        } catch (error) {
            console.error('Load error:', error);
            this.tasks = previousTasks;
        }
    }

    async createTask(title, dueAtLocal = null, dueTimeLocal = null) {
        try {
            const payload = {
                title: title.trim(),
                importance: 'not-important',
                urgency: 'not-urgent',
                due_at: dueAtLocal,
                due_time: dueTimeLocal,
            };
            
            console.log('📝 Creating task:', payload);
            
            const response = await this.apiFetch(this.apiUrl, {
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
            await this.apiFetch(`${this.apiUrl}/${id}`, { method: 'DELETE' });
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
            const response = await this.apiFetch(`${this.authApiUrl}/profile`);
            if (!response.ok) return;
            this.userProfile = await response.json();
            this.populateProfileForm();
        } catch (error) {
            console.error('Profile load error:', error);
        }
    }

    async loadGoogleMailStatus() {
        try {
            const response = await this.apiFetch(`${this.authApiUrl}/google-mail/status`);
            if (!response.ok) {
                this.googleMailStatus = null;
                this.renderGoogleMailStatus();
                return;
            }
            this.googleMailStatus = await response.json();
            this.renderGoogleMailStatus();
        } catch (error) {
            console.error('Gmail status load error:', error);
            this.googleMailStatus = null;
            this.renderGoogleMailStatus();
        }
    }

    renderGoogleMailStatus() {
        const statusEl = document.getElementById('profileGmailStatus');
        const connectBtn = document.getElementById('connectGmailBtn');
        const disconnectBtn = document.getElementById('disconnectGmailBtn');
        if (!statusEl || !connectBtn || !disconnectBtn) return;

        if (!this.googleMailStatus) {
            statusEl.textContent = 'Gmail status unavailable.';
            connectBtn.disabled = false;
            disconnectBtn.disabled = true;
            return;
        }

        const configured = !!this.googleMailStatus.oauth_configured;
        const connected = !!this.googleMailStatus.connected;
        const gmailEmail = this.googleMailStatus.gmail_email || 'Unknown';

        if (!configured) {
            statusEl.textContent = 'Google OAuth not configured on server.';
        } else if (connected) {
            statusEl.textContent = `Connected: ${gmailEmail}`;
        } else {
            statusEl.textContent = 'Not connected. Connect once to send reminders from your Gmail.';
        }

        connectBtn.disabled = !configured || connected;
        disconnectBtn.disabled = !connected;
    }

    async connectGmail() {
        try {
            const response = await this.apiFetch(`${this.authApiUrl}/google-mail/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || 'Unable to start Gmail OAuth');
                return;
            }

            const popup = window.open(data.auth_url, 'gmail_oauth', 'width=520,height=700');
            if (!popup) {
                alert('Popup blocked. Please allow popups and try again.');
                return;
            }

            if (this.googlePopupPoller) clearInterval(this.googlePopupPoller);
            this.googlePopupPoller = setInterval(async () => {
                if (popup.closed) {
                    clearInterval(this.googlePopupPoller);
                    this.googlePopupPoller = null;
                    await this.loadGoogleMailStatus();
                }
            }, 1000);
        } catch (error) {
            console.error('Gmail connect error:', error);
            alert('Unable to connect Gmail right now.');
        }
    }

    async disconnectGmail() {
        try {
            const response = await this.apiFetch(`${this.authApiUrl}/google-mail/disconnect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}),
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || 'Unable to disconnect Gmail');
                return;
            }
            await this.loadGoogleMailStatus();
        } catch (error) {
            console.error('Gmail disconnect error:', error);
            alert('Unable to disconnect Gmail right now.');
        }
    }

    splitPhoneForDisplay(phone) {
        const knownCodes = ['+91', '+1', '+86'];
        const raw = (phone || '').trim();
        if (!raw) {
            return { countryCode: '+91', localNumber: '' };
        }
        for (const code of knownCodes) {
            if (raw.startsWith(code)) {
                return {
                    countryCode: code,
                    localNumber: raw.slice(code.length).replace(/\D/g, ''),
                };
            }
        }
        return {
            countryCode: '+91',
            localNumber: raw.replace(/\D/g, ''),
        };
    }

    composeE164Phone(localOrE164, countryCode = '+91') {
        const raw = (localOrE164 || '').trim();
        if (!raw) return null;

        let candidate = '';
        if (raw.startsWith('+')) {
            candidate = `+${raw.slice(1).replace(/\D/g, '')}`;
        } else {
            const digits = raw.replace(/\D/g, '');
            candidate = `${countryCode}${digits}`;
        }

        return /^\+[1-9]\d{7,14}$/.test(candidate) ? candidate : null;
    }

    populateProfileForm() {
        const methodEl = document.getElementById('profileNotificationMethod');
        const countryEl = document.getElementById('profilePhoneCountry');
        const phoneEl = document.getElementById('profilePhone');
        if (!methodEl || !countryEl || !phoneEl || !this.userProfile) return;

        methodEl.value = this.userProfile.notification_preference || 'email';
        const split = this.splitPhoneForDisplay(this.userProfile.phone || '');
        if ([...countryEl.options].some((opt) => opt.value === split.countryCode)) {
            countryEl.value = split.countryCode;
        } else {
            countryEl.value = '+91';
        }
        phoneEl.value = split.localNumber;
    }

    async saveUserProfile() {
        const methodEl = document.getElementById('profileNotificationMethod');
        const countryEl = document.getElementById('profilePhoneCountry');
        const phoneEl = document.getElementById('profilePhone');
        if (!methodEl || !countryEl || !phoneEl) return;

        const localPhone = phoneEl.value.trim();
        const composedPhone = localPhone ? this.composeE164Phone(localPhone, countryEl.value || '+91') : null;
        if (localPhone && !composedPhone) {
            alert('Enter a valid phone number (digits only) with selected country code');
            return;
        }

        const payload = {
            notification_preference: methodEl.value || 'email',
            phone: composedPhone,
            phone_country: countryEl.value || '+91',
        };

        try {
            const response = await this.apiFetch(`${this.authApiUrl}/profile`, {
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

    async sendTestSms() {
        const countryEl = document.getElementById('profilePhoneCountry');
        const phoneEl = document.getElementById('profilePhone');
        const localPhone = (phoneEl?.value || '').trim();
        if (!localPhone) {
            alert('Enter phone number first');
            return;
        }
        const phone = this.composeE164Phone(localPhone, countryEl?.value || '+91');
        if (!phone) {
            alert('Enter a valid phone number (digits only) with selected country code');
            return;
        }

        try {
            const response = await this.apiFetch(`${this.authApiUrl}/sms/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone, phone_country: countryEl?.value || '+91' }),
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || 'Failed to send test SMS');
                return;
            }
            alert(`SMS sent to ${data.phone}`);
        } catch (error) {
            console.error('Test SMS error:', error);
            alert('Unable to send test SMS right now');
        }
    }

    async toggleTask(id) {
        try {
            const response = await this.apiFetch(`${this.apiUrl}/${id}/complete`, {
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
    async renderTasks() {
        const list = document.getElementById('tasksList');
        const count = document.getElementById('taskCount');

        let filtered = this.applyFilter(this.tasks);

        if (this.selectedDate) {
            filtered = filtered.filter((t) => {
                const d = this.getTaskReferenceDate(t);
                if (!d) return false;
                return this.getLocalDateKey(d) === this.selectedDate;
            });
        }

        filtered = await this.sortTasksForDisplay(filtered);

        const active = filtered.filter((t) => !t.completed);
        const completed = filtered.filter((t) => t.completed);
        const recommendedIds = new Set(this.getRecommendedTaskIds(active));

        count.textContent = `${active.length} tasks`;

        if (active.length === 0 && completed.length === 0) {
            list.innerHTML = '<div class="empty-state"><p>No tasks. Add one to get started.</p></div>';
            this.renderRecommendedSection([]);
            return;
        }

        let html = '';
        active.forEach((task) => {
            html += this.renderTaskItem(task, recommendedIds.has(task.id));
        });

        if (completed.length > 0) {
            html += '<div style="opacity:0.5">';
            completed.forEach((task) => {
                html += this.renderTaskItem(task, false);
            });
            html += '</div>';
        }

        list.innerHTML = html;
        this.renderRecommendedSection(active);
        this.applyMatrixLabels();
        this.attachListeners();
    }

    renderTaskItem(task, isRecommended = false) {
        const text = task.title || task.text;
        const timeLabel = this.formatDueTimeLabel(task?.due_time);
        const matrix = this.getMatrixClass(task);
        const checked = task.completed ? 'checked' : '';
        const list = this.getTaskList(task.id);
        const dueMeta = this.formatDueMeta(task);
        const splitHint = this.currentEmotion === 'stressed' && (text || '').length >= 40
            ? '<span class="task-meta hint">Split into subtasks</span>'
            : '';
        const recommendedClass = isRecommended ? 'emotion-suggested' : '';
        const recommendedBadge = isRecommended ? '<span class="task-meta recommended-tag">Recommended</span>' : '';

        return `
            <div class="task-item ${task.completed ? 'completed' : ''} ${matrix} ${recommendedClass}" data-id="${task.id}">
                <input type="checkbox" class="task-checkbox" ${checked} />
                <div class="task-main">
                    <span class="task-name">${this.escape(text)}${timeLabel}</span>
                    ${dueMeta ? `<span class="task-meta ${dueMeta.overdue ? 'overdue' : ''}">${this.escape(dueMeta.label)}</span>` : ''}
                    ${recommendedBadge}
                    ${splitHint}
                </div>

                <div class="task-controls">
                    <select class="task-list" data-id="${task.id}" title="Set list">
                        <option value="inbox" ${list === 'inbox' ? 'selected' : ''}>Inbox</option>
                        <option value="work" ${list === 'work' ? 'selected' : ''}>Work</option>
                        <option value="study" ${list === 'study' ? 'selected' : ''}>Study</option>
                        <option value="personal" ${list === 'personal' ? 'selected' : ''}>Personal</option>
                    </select>

                    <select class="task-importance" data-id="${task.id}" title="Set importance">
                        <option value="important" ${task.importance === 'important' ? 'selected' : ''}>Important</option>
                        <option value="not-important" ${task.importance === 'not-important' ? 'selected' : ''}>Not Important</option>
                    </select>

                    <select class="task-urgency" data-id="${task.id}" title="Set urgency">
                        <option value="urgent" ${task.urgency === 'urgent' ? 'selected' : ''}>Urgent</option>
                        <option value="not-urgent" ${task.urgency === 'not-urgent' ? 'selected' : ''}>Not Urgent</option>
                    </select>
                </div>

                <div class="task-actions">
                    <button class="task-delete" data-id="${task.id}" title="Delete">x</button>
                </div>
            </div>
        `;
    }

    formatDueTimeLabel(dueTime) {
        const raw = String(dueTime || '').trim();
        if (!raw) return '';
        const normalized = raw.length >= 5 ? raw.slice(0, 5) : raw;
        return ` (${this.escape(normalized)})`;
    }

    formatDueTimeValue(dueTime) {
        const raw = String(dueTime || '').trim();
        if (!raw) return '';
        return raw.length >= 5 ? raw.slice(0, 5) : raw;
    }

    getRecommendedTaskIds(activeTasks) {
        if (!this.currentEmotion) return [];
        const ranked = (activeTasks || [])
            .map((task) => ({
                task,
                score: this.scoreTaskForEmotion(task, this.currentEmotion),
            }))
            .sort((a, b) => b.score - a.score);
        return ranked.slice(0, 3).map((entry) => entry.task.id);
    }

    scoreTaskForEmotion(task, emotion) {
        const imp = task.importance === 'important';
        const urg = task.urgency === 'urgent';
        const title = String(task.title || '').trim();
        const complexity = Math.min(1, title.length / 40); // 0..1 proxy

        if (emotion === 'focused') {
            return (imp ? 2 : 0) + (urg ? 1 : 0) + complexity;
        }
        if (emotion === 'stressed') {
            const calmness = 1 - complexity;
            return (urg ? 2 : 0) + (imp ? 1 : 0) + calmness;
        }
        const mid = 1 - Math.abs(complexity - 0.5);
        return (imp ? 1 : 0) + (urg ? 1 : 0) + mid;
    }

    renderRecommendedSection(activeTasks) {
        const section = document.getElementById('recommendedSection');
        const list = document.getElementById('recommendedList');
        const hint = document.getElementById('recommendedHint');
        const status = document.getElementById('feedbackStatus');
        if (!section || !list) return;

        if (!this.currentEmotion || !activeTasks || activeTasks.length === 0) {
            section.style.display = 'none';
            list.innerHTML = '';
            if (hint) hint.textContent = '';
            if (status) status.textContent = '';
            return;
        }

        const topThree = activeTasks.slice(0, 3);
        section.style.display = topThree.length ? 'block' : 'none';
        if (status) status.textContent = '';
        if (hint) {
            if (this.currentEmotion === 'stressed') {
                hint.textContent = 'Pause, breathe, and pick one small urgent task. You can do this.';
            } else if (this.currentEmotion === 'focused') {
                hint.textContent = 'Focus mode: tackle the hardest high-impact task first.';
            } else {
                hint.textContent = 'Neutral mode: aim for steady progress with medium-priority tasks.';
            }
        }
        list.innerHTML = topThree
            .map((task, idx) => `<li>${idx + 1}. ${this.escape(task.title || '')}</li>`)
            .join('');
    }

    recordRecommendationFeedback(helpful) {
        const status = document.getElementById('feedbackStatus');
        const payload = {
            helpful: !!helpful,
            emotion: this.currentEmotion || 'neutral',
            ts: new Date().toISOString(),
        };
        try {
            const existing = JSON.parse(localStorage.getItem('recommendationFeedback') || '[]');
            existing.push(payload);
            localStorage.setItem('recommendationFeedback', JSON.stringify(existing));
        } catch {
            // Ignore storage errors.
        }
        if (status) {
            status.textContent = helpful ? 'Thanks for the feedback.' : 'Got it. We will adjust.';
        }
    }

    getMatrixClass(task) {
        const imp = task.importance === 'important';
        const urg = task.urgency === 'urgent';
        if (imp && urg) return 'imp-urg';
        if (imp && !urg) return 'imp-nurg';
        if (!imp && urg) return 'nimp-urg';
        return 'nimp-nurg';
    }

    getMatrixLabels() {
        if (this.matrixType === 'impact-effort') {
            return {
                importanceLabel: 'High Impact',
                notImportanceLabel: 'Low Impact',
                urgencyLabel: 'High Effort',
                notUrgencyLabel: 'Low Effort',
                importanceTitle: 'Set impact',
                urgencyTitle: 'Set effort',
            };
        }
        if (this.matrixType === 'moscow') {
            return {
                importanceLabel: 'Must',
                notImportanceLabel: 'Should',
                urgencyLabel: 'Could',
                notUrgencyLabel: "Won't",
                importanceTitle: 'Set must/should',
                urgencyTitle: 'Set could/won’t',
            };
        }

        return {
            importanceLabel: 'Important',
            notImportanceLabel: 'Not Important',
            urgencyLabel: 'Urgent',
            notUrgencyLabel: 'Not Urgent',
            importanceTitle: 'Set importance',
            urgencyTitle: 'Set urgency',
        };
    }

    applyMatrixLabels() {
        const labels = this.getMatrixLabels();

        document.querySelectorAll('.task-importance').forEach(select => {
            select.title = labels.importanceTitle;
            const high = select.querySelector('option[value="important"]');
            const low = select.querySelector('option[value="not-important"]');
            if (high) high.textContent = labels.importanceLabel;
            if (low) low.textContent = labels.notImportanceLabel;
        });

        document.querySelectorAll('.task-urgency').forEach(select => {
            select.title = labels.urgencyTitle;
            const high = select.querySelector('option[value="urgent"]');
            const low = select.querySelector('option[value="not-urgent"]');
            if (high) high.textContent = labels.urgencyLabel;
            if (low) low.textContent = labels.notUrgencyLabel;
        });
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
            const response = await this.apiFetch(`${this.apiUrl}/${id}`, {
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

    getEmotionPriorityRank(task) {
        const imp = task.importance === 'important';
        const urg = task.urgency === 'urgent';

        // Deterministic, explainable rules for viva.
        if (this.currentEmotion === 'stressed') {
            // Short + urgent first; lower load before long tasks.
            if (urg && !imp) return 1;
            if (urg && imp) return 2;
            if (!urg && !imp) return 3;
            return 4;
        }

        if (this.currentEmotion === 'focused') {
            // High-priority complex (important) first, then long-term work.
            if (imp && urg) return 1;
            if (imp && !urg) return 2;
            if (!imp && urg) return 3;
            return 4;
        }

        // Neutral: medium-priority and routine/organizing tasks first.
        if ((imp && !urg) || (!imp && urg)) return 1;
        if (!imp && !urg) return 2;
        return 3;
    }

    compareTaskEffort(a, b) {
        const aLen = (a.title || '').trim().length;
        const bLen = (b.title || '').trim().length;

        if (this.currentEmotion === 'stressed') {
            return aLen - bLen;
        }
        if (this.currentEmotion === 'focused') {
            return bLen - aLen;
        }

        const aTime = new Date(a.created_at || 0).getTime();
        const bTime = new Date(b.created_at || 0).getTime();
        return aTime - bTime;
    }

    async sortTasksForDisplay(tasks) {
        return [...(tasks || [])].sort((a, b) => {
            const rankDiff = this.getEmotionPriorityRank(a) - this.getEmotionPriorityRank(b);
            if (rankDiff !== 0) return rankDiff;

            const matrixDiff = this.getMatrixRank(a) - this.getMatrixRank(b);
            if (matrixDiff !== 0) return matrixDiff;

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
        const dueTimeValue = this.formatDueTimeValue(task?.due_time);

        content.innerHTML = `
            <div class="detail-row">
                <div class="detail-label">Title</div>
                <div class="detail-value">${this.escape(task.title || '')}</div>
            </div>
            ${dueTimeValue ? `
            <div class="detail-row">
                <div class="detail-label">Time</div>
                <div class="detail-value">${this.escape(dueTimeValue)}</div>
            </div>` : ''}
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

                <div class="detail-actions">
                    <button class="btn-secondary" id="detailClear">Clear</button>
                    <button class="btn-primary" id="detailSave">Save</button>
                </div>
                <div class="detail-status" id="detailStatus"></div>
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
            this.updateTaskDetails(task.id, true);
        });
    }

    async updateTaskDetails(id, clearAll = false) {
        const task = this.tasks.find(t => t.id === id);
        if (!task) return;

        const dueRaw = document.getElementById('detailDue').value;
        const reminderRaw = document.getElementById('detailReminder').value;
        const method = document.getElementById('detailMethod').value;
        const statusEl = document.getElementById('detailStatus');
        const saveBtn = document.getElementById('detailSave');
        const clearBtn = document.getElementById('detailClear');

        const updateData = {
            due_at: dueRaw || null,
            reminder_at: reminderRaw || null,
            reminder_method: method || null,
            // Use the single profile phone source for SMS reminders.
            reminder_phone: null,
        };

        if (clearAll) {
            updateData.due_at = null;
            updateData.reminder_at = null;
            updateData.reminder_method = null;
            updateData.reminder_phone = null;
        }

        try {
            if (statusEl) {
                statusEl.textContent = clearAll ? 'Clearing…' : 'Saving…';
                statusEl.classList.remove('error');
            }
            if (saveBtn) saveBtn.disabled = true;
            if (clearBtn) clearBtn.disabled = true;

            const response = await this.apiFetch(`${this.apiUrl}/${id}`, {
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
                if (statusEl) statusEl.textContent = 'Saved';
            } else {
                let message = 'Unable to save changes.';
                try {
                    const data = await response.json();
                    if (data && data.error) message = data.error;
                } catch {
                    // ignore
                }
                if (statusEl) {
                    statusEl.textContent = message;
                    statusEl.classList.add('error');
                } else {
                    alert(message);
                }
            }
        } catch (error) {
            console.error('Detail update error:', error);
            if (statusEl) {
                statusEl.textContent = 'Save failed. Check connection and try again.';
                statusEl.classList.add('error');
            } else {
                alert('Save failed. Check connection and try again.');
            }
        } finally {
            if (saveBtn) saveBtn.disabled = false;
            if (clearBtn) clearBtn.disabled = false;
        }
    }

    toLocalInputValue(date) {
        const pad = (n) => String(n).padStart(2, '0');
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    startReminderLoop() {
        const run = async () => {
            try {
                const res = await this.apiFetch(`${this.apiUrl}/reminders/dispatch`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({}),
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

        setInterval(run, 120000);
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

        // Ensure any previous stream is fully closed before opening a new one.
        this.stopCamera();
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
        const video = document.getElementById('videoFeed');
        if (video) {
            const stream = video.srcObject;
            if (stream && typeof stream.getTracks === 'function') {
                stream.getTracks().forEach(t => t.stop());
            }
            video.pause();
            video.srcObject = null;
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

        let timeoutId = null;
        try {
            const controller = new AbortController();
            timeoutId = setTimeout(() => controller.abort(), 6000);
            // Try real API
            const res = await this.apiFetch(`${this.apiUrl}/emotion-scan`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
                body: JSON.stringify({ image: base64 }),
            });
            if (res.ok) {
                const result = await res.json();
                this.showEmotionResult(result);
                return;
            }
        } catch (err) {
            console.log('API unavailable, using mock');
        } finally {
            if (timeoutId) clearTimeout(timeoutId);
        }

        // Fallback to mock
        this.showEmotionResult(this.getMockEmotion());
    }
    getMockEmotion() {
        return { emotion: 'neutral', confidence: 0.6 };
    }

    formatEmotionLabel(label) {
        const text = String(label || '').trim();
        if (!text) return '';
        return `${text.charAt(0).toUpperCase()}${text.slice(1)}`;
    }

    resolveEmotionDisplay(result, safeEmotion) {
        const raw = String(
            (result && result.debug && (result.debug.best_emotion || result.debug.dominant_emotion)) || result?.emotion || ''
        ).trim().toLowerCase();

        if (['happy', 'surprise', 'smile'].includes(raw)) {
            return {
                label: 'Happy',
                icon: '\u{1F60A}',
                message: 'Happy mode: great time for creative or challenging work while your energy is high.',
            };
        }

        if (safeEmotion === 'focused') {
            return {
                label: 'Focused',
                icon: '\u{1F3AF}',
                message: 'Focus mode: go for a high-impact, challenging task while your energy is up.',
            };
        }
        if (safeEmotion === 'stressed') {
            return {
                label: 'Stressed',
                icon: '\u{1F623}',
                message: 'Stress mode: take a slow breath, then pick one small urgent task. You can do this.',
            };
        }
        return {
            label: 'Neutral',
            icon: '\u{1F610}',
            message: 'Neutral mode: steady progress with medium-priority tasks and light planning.',
        };
    }

    showEmotionResult(result) {
        this.closeCamera();

        const safeEmotion = ['focused', 'stressed', 'neutral'].includes(result.emotion)
            ? result.emotion
            : 'neutral';
        const display = this.resolveEmotionDisplay(result, safeEmotion);
        this.pendingEmotionResult = { ...result, emotion: safeEmotion, displayLabel: display.label, displayIcon: display.icon };

        const breathWrap = document.getElementById('breathWrap');
        if (breathWrap) {
            breathWrap.style.display = safeEmotion === 'stressed' ? 'flex' : 'none';
        }

        document.getElementById('resultIcon').textContent = display.icon;
        document.getElementById('resultEmotion').textContent = display.label;
        document.getElementById('resultConfidence').textContent = Math.round((result.confidence || 0) * 100);
        document.getElementById('resultMessage').textContent = display.message;
        this.renderEmotionDebug(result);

        // Show result modal
        document.getElementById('resultModal').classList.add('show');
        document.getElementById('modalOverlay').classList.add('show');
    }

    applyEmotionToTasks() {
        if (!this.pendingEmotionResult) return;

        this.currentEmotion = this.pendingEmotionResult.emotion;
        const icons = { focused: '\u{1F3AF}', stressed: '\u{1F623}', neutral: '\u{1F610}' };
        const badge = document.getElementById('emotionBadge');
        const displayLabel = this.pendingEmotionResult.displayLabel || this.formatEmotionLabel(this.currentEmotion);
        const displayIcon = this.pendingEmotionResult.displayIcon || icons[this.currentEmotion] || 'N';
        this.currentEmotionLabel = displayLabel;
        document.getElementById('emotionIcon').textContent = displayIcon;
        document.getElementById('emotionLabel').textContent = displayLabel;
        badge.style.display = 'flex';

        this.renderTasks();
        this.closeResult();
    }

    closeResult() {
        // Defensive cleanup in case a stream remained active.
        this.stopCamera();
        this.pendingEmotionResult = null;
        document.getElementById('resultModal').classList.remove('show');
        document.getElementById('modalOverlay').classList.remove('show');
    }

    renderEmotionDebug(result) {
        const wrap = document.getElementById('emotionDebug');
        if (!wrap) return;
        const debug = result && result.debug ? result.debug : null;
        if (!debug) {
            wrap.style.display = 'none';
            return;
        }
        const scores = debug.scores || {};
        const scorePairs = Object.keys(scores)
            .map((k) => `${k}:${Math.round(scores[k])}`)
            .join(', ');
        wrap.style.display = 'block';
        document.getElementById('debugSource').textContent = debug.source || '-';
        document.getElementById('debugDominant').textContent = debug.dominant_emotion || '-';
        document.getElementById('debugBest').textContent = debug.best_emotion || '-';
        document.getElementById('debugScores').textContent = scorePairs || '-';
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
            } else {
                msg.textContent = 'Analyzing...';
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
        const matrixSelect = document.getElementById('matrixSelect');
        if (matrixSelect) {
            matrixSelect.value = this.matrixType;
            matrixSelect.addEventListener('change', (e) => {
                this.matrixType = e.target.value || 'eisenhower';
                this.saveMatrixType(this.matrixType);
                this.renderTasks();
            });
        }

        // Add task
        const input = document.getElementById('taskInput');
        const dueInput = document.getElementById('taskDueInput');
        const timeInput = document.getElementById('taskTimeInput');
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                const dueAtLocal = dueInput?.value || null;
                const dueTimeLocal = timeInput?.value || null;
                const task = await this.createTask(input.value, dueAtLocal, dueTimeLocal);
                if (task) {
                    this.tasks.unshift(task);
                    this.renderTasks();
                    input.value = '';
                    if (dueInput) dueInput.value = '';
                    if (timeInput) timeInput.value = '';
                    this.generateCalendar();
                }
            }
        });

        const leftToggle = document.getElementById('toggleLeftPanel');
        const rightToggle = document.getElementById('toggleRightPanel');
        const leftPanel = document.getElementById('sidebarLeft');
        const rightPanel = document.getElementById('sidebarRight');

        leftToggle?.addEventListener('click', () => {
            if (leftPanel) leftPanel.classList.toggle('visible');
            if (rightPanel) rightPanel.classList.remove('visible');
        });

        rightToggle?.addEventListener('click', () => {
            if (rightPanel) rightPanel.classList.toggle('visible');
            if (leftPanel) leftPanel.classList.remove('visible');
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
        document.getElementById('sendTestSmsBtn')?.addEventListener('click', () => {
            this.sendTestSms();
        });
        document.getElementById('connectGmailBtn')?.addEventListener('click', () => {
            this.connectGmail();
        });
        document.getElementById('disconnectGmailBtn')?.addEventListener('click', () => {
            this.disconnectGmail();
        });

        // Emotion scan
        document.getElementById('emotionScanBtn').addEventListener('click', () => {
            this.openCamera();
        });

        // Theme toggle
        document.getElementById('themeToggle')?.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Camera controls
        document.getElementById('closeCamera').addEventListener('click', () => this.closeCamera());
        document.getElementById('cancelCamera').addEventListener('click', () => this.closeCamera());
        document.getElementById('captureImage')?.addEventListener('click', () => this.analyzeEmotion());

        // Result modal
        document.getElementById('closeResult').addEventListener('click', () => this.closeResult());
        document.getElementById('rejectEmotion').addEventListener('click', () => this.closeResult());
        document.getElementById('applyEmotion').addEventListener('click', () => this.applyEmotionToTasks());

        // Emotion badge
        document.getElementById('clearEmotionBtn').addEventListener('click', () => this.clearEmotion());

        // Recommendation feedback
        document.getElementById('feedbackYes')?.addEventListener('click', () => {
            this.recordRecommendationFeedback(true);
        });
        document.getElementById('feedbackNo')?.addEventListener('click', () => {
            this.recordRecommendationFeedback(false);
        });

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
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('userEmail');
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







