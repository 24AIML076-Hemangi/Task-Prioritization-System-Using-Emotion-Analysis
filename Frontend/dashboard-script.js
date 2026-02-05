/* ============================================
   TaskPrioritize - Minimal Script
   Clean, Functional Task Management
   ============================================ */

class TaskManager {
    constructor() {
        this.tasks = [];
        this.userId = null;
        this.apiUrl = 'http://localhost:5000/api/tasks';
        this.currentEmotion = null;
        this.cameraStream = null;
        this.calendarMonth = new Date().getMonth();
        this.calendarYear = new Date().getFullYear();
        this.selectedDate = null;

        this.init();
    }

    async init() {
        // Check login
        if (!localStorage.getItem('isLoggedIn')) {
            window.location.href = 'login.html';
            return;
        }

        this.userId = localStorage.getItem('userName') || 'User';
        document.getElementById('userInfo').textContent = this.userId;

        await this.loadTasks();
        this.setupEventListeners();
        this.generateCalendar();
        this.renderTasks();
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

    async createTask(title) {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    title: title.trim(),
                    importance: 'not-important',
                    urgency: 'not-urgent',
                }),
            });

            if (response.ok) {
                return await response.json();
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
            this.renderTasks();
        } catch (error) {
            console.error('Delete error:', error);
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

        let filtered = this.tasks;

        // Filter by selected date if any
        if (this.selectedDate) {
            filtered = filtered.filter(t => {
                const d = new Date(t.created_at || t.createdAt);
                return d.toISOString().slice(0, 10) === this.selectedDate;
            });
        }

        // Separate completed and active
        const active = filtered.filter(t => !t.completed);
        const completed = filtered.filter(t => t.completed);

        count.textContent = active.length;

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

        list.innerHTML = html;
        this.attachListeners();
    }

    renderTaskItem(task) {
        const text = task.title || task.text;
        const matrix = this.getMatrixClass(task);
        const checked = task.completed ? 'checked' : '';

        return `
            <div class="task-item ${task.completed ? 'completed' : ''} ${matrix}" data-id="${task.id}">
                <input type="checkbox" class="task-checkbox" ${checked} />
                <span class="task-name">${this.escape(text)}</span>
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

    attachListeners() {
        // Checkboxes
        document.querySelectorAll('.task-checkbox').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const id = parseInt(e.target.closest('.task-item').dataset.id);
                this.toggleTask(id);
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
        const now = new Date();

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
            const iso = date.toISOString().slice(0, 10);
            const isSelected = this.selectedDate === iso ? 'selected' : '';
            html += `<button class="cal-day ${isSelected}" data-date="${iso}">${d}</button>`;
        }

        html += '</div>';
        container.innerHTML = html;

        // Attach day click handlers
        container.querySelectorAll('.cal-day[data-date]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const date = e.target.dataset.date;
                this.selectedDate = this.selectedDate === date ? null : date;
                this.generateCalendar();
                this.renderTasks();
            });
        });
    }

    /* ============================================
       Camera & Emotion
       ============================================ */

    async openCamera() {
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
            msg.textContent = 'Ready to scan. Click "Scan me" when ready.';
        } catch (error) {
            msg.textContent = `Camera error: ${error.message}`;
        }
    }

    stopCamera() {
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

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        const base64 = canvas.toDataURL('image/jpeg').split(',')[1];

        try {
            // Try real API
            const res = await fetch('http://localhost:5000/emotion-scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: base64, user_id: this.userId }),
                timeout: 5000,
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

        this.currentEmotion = result.emotion;

        document.getElementById('resultIcon').textContent = icons[result.emotion];
        document.getElementById('resultEmotion').textContent = result.emotion;
        document.getElementById('resultConfidence').textContent = Math.round(result.confidence * 100);
        document.getElementById('resultMessage').textContent = messages[result.emotion];

        // Show emotion badge
        const badge = document.getElementById('emotionBadge');
        document.getElementById('emotionIcon').textContent = icons[result.emotion];
        document.getElementById('emotionLabel').textContent = result.emotion;
        badge.style.display = 'flex';

        // Show result modal
        document.getElementById('resultModal').classList.add('show');
        document.getElementById('modalOverlay').classList.add('show');
    }

    closeResult() {
        document.getElementById('resultModal').classList.remove('show');
        document.getElementById('modalOverlay').classList.remove('show');
    }

    clearEmotion() {
        this.currentEmotion = null;
        document.getElementById('emotionBadge').style.display = 'none';
    }

    /* ============================================
       EVENT LISTENERS
       ============================================ */

    setupEventListeners() {
        // Add task
        const input = document.getElementById('taskInput');
        input.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter' && input.value.trim()) {
                const task = await this.createTask(input.value);
                if (task) {
                    this.tasks.unshift(task);
                    this.renderTasks();
                    input.value = '';
                }
            }
        });

        // Toggle calendar (mobile)
        document.getElementById('toggleCalendarBtn')?.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('visible');
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
        document.getElementById('closeResultBtn').addEventListener('click', () => this.closeResult());

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
