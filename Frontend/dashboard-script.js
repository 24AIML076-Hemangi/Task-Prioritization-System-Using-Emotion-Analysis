/* ============================================
   Task Dashboard - Main Application
   Emotion-based task prioritization system
   ============================================ */

class TaskDashboard {
    constructor() {
        this.tasks = [];
        this.currentEmotion = null;
        this.currentConfidence = null;
        this.cameraStream = null;
        this.userId = null;
        this.apiUrl = 'http://localhost:5000/api/tasks';

        this.initializeAfterDOM();
    }

    initializeAfterDOM() {
        // Check login state
        if (!localStorage.getItem('isLoggedIn')) {
            console.warn('User not logged in. Redirecting to login.');
            window.location.href = 'login.html';
            return;
        }

        this.userId = localStorage.getItem('userName');
        console.log('Logged in user:', this.userId);

        this.loadTasksFromAPI();
        this.setupEventListeners();
        this.updateUserInfo();

        console.log('Dashboard initialized successfully');
    }

    /* ============================================
       Data Management - API Integration
       ============================================ */

    async loadTasksFromAPI() {
        try {
            console.log(`Fetching tasks for user: ${this.userId}`);
            const response = await fetch(`${this.apiUrl}?user_id=${this.userId}`);
            
            if (response.ok) {
                this.tasks = await response.json();
                console.log('Tasks loaded from API:', this.tasks.length, 'tasks');
            } else {
                console.warn('Failed to load tasks from API, using defaults');
                this.tasks = this.getDefaultTasks();
                // Try to create default tasks in DB
                await this.seedDefaultTasks();
            }
        } catch (error) {
            console.error('Error loading tasks from API:', error);
            this.tasks = this.getDefaultTasks();
        }

        this.renderTasks();
    }

    async seedDefaultTasks() {
        const defaults = this.getDefaultTasks();
        for (const task of defaults) {
            await this.createTaskInAPI(task.title, task.importance, task.urgency);
        }
    }

    async createTaskInAPI(title, importance = 'not-important', urgency = 'not-urgent') {
        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    title: title,
                    importance: importance,
                    urgency: urgency,
                }),
            });

            if (response.ok) {
                const newTask = await response.json();
                console.log('Task created in API:', newTask);
                return newTask;
            } else {
                console.error('Failed to create task in API');
                return null;
            }
        } catch (error) {
            console.error('Error creating task in API:', error);
            return null;
        }
    }

    async updateTaskInAPI(taskId, updates) {
        try {
            const response = await fetch(`${this.apiUrl}/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updates),
            });

            if (response.ok) {
                const updated = await response.json();
                console.log('Task updated in API:', updated);
                return updated;
            } else {
                console.error('Failed to update task in API');
                return null;
            }
        } catch (error) {
            console.error('Error updating task in API:', error);
            return null;
        }
    }

    async deleteTaskInAPI(taskId) {
        try {
            const response = await fetch(`${this.apiUrl}/${taskId}`, {
                method: 'DELETE',
            });

            if (response.ok) {
                console.log('Task deleted from API:', taskId);
                return true;
            } else {
                console.error('Failed to delete task from API');
                return false;
            }
        } catch (error) {
            console.error('Error deleting task from API:', error);
            return false;
        }
    }

    async toggleTaskInAPI(taskId, completed) {
        try {
            const response = await fetch(`${this.apiUrl}/${taskId}/complete`, {
                method: 'PATCH',
            });

            if (response.ok) {
                const updated = await response.json();
                console.log('Task completion toggled in API:', updated);
                return updated;
            } else {
                console.error('Failed to toggle task in API');
                return null;
            }
        } catch (error) {
            console.error('Error toggling task in API:', error);
            return null;
        }
    }

    loadTasks() {
        // Legacy method - kept for compatibility
        this.loadTasksFromAPI();
    }

    saveTasks() {
        // Legacy method - no longer needed with API
        // Each operation now calls API directly
    }

    getDefaultTasks() {
        return [
            { id: 1, text: 'Review project requirements', importance: 'important', urgency: 'not-urgent', completed: false, createdAt: new Date().toISOString() },
            { id: 2, text: 'Schedule team meeting', importance: 'important', urgency: 'urgent', completed: false, createdAt: new Date().toISOString() },
            { id: 3, text: 'Update documentation', importance: 'not-important', urgency: 'not-urgent', completed: false, createdAt: new Date().toISOString() },
            { id: 4, text: 'Fix reported bugs', importance: 'important', urgency: 'urgent', completed: false, createdAt: new Date().toISOString() },
            { id: 5, text: 'Reply to emails', importance: 'not-important', urgency: 'urgent', completed: false, createdAt: new Date().toISOString() },
        ];
    }

    updateUserInfo() {
        const userName = localStorage.getItem('userName') || 'User';
        document.getElementById('userInfo').textContent = userName;
    }

    /* ============================================
       Task Operations
       ============================================ */

    async addTask(text) {
        if (!text.trim()) return;

        const newTask = await this.createTaskInAPI(text.trim());
        if (newTask) {
            this.tasks.unshift(newTask);
            this.renderTasks();
            document.getElementById('taskInput').value = '';
            return newTask;
        }
    }

    async deleteTask(id) {
        const deleted = await this.deleteTaskInAPI(id);
        if (deleted) {
            this.tasks = this.tasks.filter((t) => t.id !== id);
            this.renderTasks();
        }
    }

    async toggleTask(id) {
        const task = this.tasks.find((t) => t.id === id);
        if (task) {
            const updated = await this.toggleTaskInAPI(id, !task.completed);
            if (updated) {
                task.completed = updated.completed;
                this.renderTasks();
            }
        }
    }

    sortTasksByEmotion(emotion) {
        if (!emotion) return this.tasks;

        const activeTasks = this.tasks.filter((t) => !t.completed);
        const completedTasks = this.tasks.filter((t) => t.completed);

        if (emotion === 'focused') {
            // Show high priority first - user is ready for challenging work
            activeTasks.sort((a, b) => {
                const priorityOrder = { high: 0, medium: 1, low: 2 };
                return priorityOrder[a.priority] - priorityOrder[b.priority];
            });
        } else if (emotion === 'stressed') {
            // Show low priority first - build momentum with quick wins
            activeTasks.sort((a, b) => {
                const priorityOrder = { low: 0, medium: 1, high: 2 };
                return priorityOrder[a.priority] - priorityOrder[b.priority];
            });
        } else {
            // Neutral - keep default order
            activeTasks.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        }

        return [...activeTasks, ...completedTasks];
    }

    /* ============================================
       Rendering
       ============================================ */

    renderTasks() {
        const tasksList = document.getElementById('tasksList');
        const tasksCount = document.getElementById('tasksCount');

        // Get tasks ordered by Eisenhower matrix and emotion (only within groups)
        const tasksToRender = this.getOrderedTasks();
        const activeTasks = tasksToRender.filter((t) => !t.completed);
        tasksCount.textContent = activeTasks.length;

        if (tasksToRender.length === 0) {
            tasksList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📋</div>
                    <p class="empty-text">No tasks yet. Add one to get started!</p>
                </div>
            `;
            return;
        }

        tasksList.innerHTML = tasksToRender.map((task) => this.createTaskElement(task)).join('');

        // Attach event listeners for dynamic controls
        this.attachTaskEventListeners();

        // Update visibility of emotion scan button based on rules
        this.updateEmotionButtonVisibility();
    }

    createTaskElement(task) {
        const completedClass = task.completed ? 'completed' : '';
        // Map matrix group to class for subtle visual hint
        const matrixClass = this.matrixClassFor(task);
        const taskText = task.title || task.text; // Support both API and legacy formats

        return `
            <div class="task-item ${completedClass} ${matrixClass}" data-id="${task.id}">
                <input
                    type="checkbox"
                    class="task-checkbox"
                    ${task.completed ? 'checked' : ''}
                    data-id="${task.id}"
                    aria-label="Mark task complete"
                >

                <div class="task-main">
                    <div class="task-top">
                        <span class="task-text">${this.escapeHtml(taskText)}</span>
                    </div>

                    <div class="task-controls">
                        <label class="control-label">Importance
                            <select class="select-importance" data-id="${task.id}">
                                <option value="important" ${task.importance === 'important' ? 'selected' : ''}>Important</option>
                                <option value="not-important" ${task.importance === 'not-important' ? 'selected' : ''}>Not Important</option>
                            </select>
                        </label>

                        <label class="control-label">Urgency
                            <select class="select-urgency" data-id="${task.id}">
                                <option value="urgent" ${task.urgency === 'urgent' ? 'selected' : ''}>Urgent</option>
                                <option value="not-urgent" ${task.urgency === 'not-urgent' ? 'selected' : ''}>Not Urgent</option>
                            </select>
                        </label>

                        <div class="task-meta">
                            <span class="task-created">${this.formatDate(task.created_at || task.createdAt)}</span>
                        </div>
                    </div>
                </div>

                <button
                    class="task-delete-btn"
                    data-id="${task.id}"
                    title="Delete task"
                    aria-label="Delete task"
                >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;
    }

    attachTaskEventListeners() {
        // Checkbox handlers
        document.querySelectorAll('.task-checkbox').forEach((checkbox) => {
            checkbox.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                if (!Number.isNaN(id)) this.toggleTask(id);
            });
        });

        // Delete handlers
        document.querySelectorAll('.task-delete-btn').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                const id = parseInt(e.currentTarget.dataset.id);
                if (!Number.isNaN(id) && confirm('Delete this task?')) {
                    this.deleteTask(id);
                }
            });
        });

        // Importance select handlers
        document.querySelectorAll('.select-importance').forEach((sel) => {
            sel.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                const val = e.target.value;
                const task = this.tasks.find((t) => t.id === id);
                if (task) {
                    task.importance = val;
                    this.updateTaskInAPI(id, { importance: val });
                    this.renderTasks();
                }
            });
        });

        // Urgency select handlers
        document.querySelectorAll('.select-urgency').forEach((sel) => {
            sel.addEventListener('change', (e) => {
                const id = parseInt(e.target.dataset.id);
                const val = e.target.value;
                const task = this.tasks.find((t) => t.id === id);
                if (task) {
                    task.urgency = val;
                    this.updateTaskInAPI(id, { urgency: val });
                    this.renderTasks();
                }
            });
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        }
    }

    // Return a small matrix class for subtle visual styling
    matrixClassFor(task) {
        if (!task) return '';
        const imp = task.importance === 'important' ? 'imp' : 'nimp';
        const urg = task.urgency === 'urgent' ? 'urg' : 'nurg';
        return `matrix-${imp}-${urg}`;
    }

    // Estimate effort from task text length (simple heuristic)
    estimateEffort(task) {
        if (!task) return 'medium';
        const taskText = task.title || task.text || '';
        const len = taskText.trim().length;
        if (len <= 40) return 'easy';
        if (len <= 100) return 'medium';
        return 'hard';
    }

    // Return tasks ordered by Eisenhower matrix and within-group emotion logic
    getOrderedTasks() {
        const active = this.tasks.filter((t) => !t.completed);
        const completed = this.tasks.filter((t) => t.completed);

        // Group by matrix categories
        const g1 = []; // Important + Urgent
        const g2 = []; // Important + Not Urgent
        const g3 = []; // Not Important + Urgent
        const g4 = []; // Not Important + Not Urgent

        active.forEach((t) => {
            const imp = t.importance === 'important';
            const urg = t.urgency === 'urgent';
            if (imp && urg) g1.push(t);
            else if (imp && !urg) g2.push(t);
            else if (!imp && urg) g3.push(t);
            else g4.push(t);
        });

        // Within each group, respect manual selection (already used), preserve creation order
        const reorderWithin = (group) => {
            if (!this.currentEmotion) {
                // default: most recent first
                return group.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
            }

            if (this.currentEmotion === 'neutral') return group;

            // For emotion-based reorder only within group
            if (this.currentEmotion === 'stressed') {
                // show easier tasks first
                return group.sort((a, b) => {
                    const ea = this.estimateEffort(a) === 'easy' ? 0 : 1;
                    const eb = this.estimateEffort(b) === 'easy' ? 0 : 1;
                    if (ea !== eb) return ea - eb;
                    return new Date(b.createdAt) - new Date(a.createdAt);
                });
            }

            if (this.currentEmotion === 'focused') {
                // show harder (higher effort) tasks first
                return group.sort((a, b) => {
                    const ra = this.estimateEffort(a) === 'hard' ? 0 : 1;
                    const rb = this.estimateEffort(b) === 'hard' ? 0 : 1;
                    if (ra !== rb) return ra - rb;
                    return new Date(b.createdAt) - new Date(a.createdAt);
                });
            }

            return group;
        };

        const ordered = [
            ...reorderWithin(g1),
            ...reorderWithin(g2),
            ...reorderWithin(g3),
            ...reorderWithin(g4),
            ...completed.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)),
        ];

        return ordered;
    }

    // Show/hide emotion scan FAB according to rules
    updateEmotionButtonVisibility() {
        try {
            const btn = document.getElementById('emotionScanBtn');
            if (!btn) return;

            const importantTasks = this.tasks.filter((t) => t.importance === 'important');
            const importantCount = importantTasks.length;
            const pendingImportant = importantTasks.filter((t) => !t.completed).length;

            const shouldShow = importantCount > 5 || (importantCount > 0 && pendingImportant === importantCount);

            btn.style.display = shouldShow ? 'flex' : 'none';
            console.log('Emotion button visibility:', shouldShow);
        } catch (e) {
            console.error('Error updating emotion button visibility', e);
        }
    }

    /* ============================================
       Camera & Emotion Detection
       ============================================ */

    async openCamera() {
        const modal = document.getElementById('cameraModal');
        const video = document.getElementById('videoFeed');
        const message = document.getElementById('cameraMessage');

        modal.classList.add('active');
        document.getElementById('modalBackdrop').classList.add('active');

        message.textContent = 'Requesting camera access...';

        try {
            console.log('Requesting camera access...');
            this.cameraStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                },
            });

            video.srcObject = this.cameraStream;
            await video.play();

            message.textContent = 'Camera ready. Click "Capture" to scan your emotion.';
            console.log('Camera opened successfully');
        } catch (error) {
            message.textContent = `Camera access denied: ${error.message}`;
            message.style.color = '#dc2626';
            console.error('Camera error:', error);
        }
    }

    stopCamera() {
        if (this.cameraStream) {
            this.cameraStream.getTracks().forEach((track) => {
                track.stop();
                console.log('Camera track stopped');
            });
            this.cameraStream = null;
        }
    }

    closeCamera() {
        this.stopCamera();
        document.getElementById('cameraModal').classList.remove('active');
        document.getElementById('modalBackdrop').classList.remove('active');
    }

    captureImage() {
        const video = document.getElementById('videoFeed');
        const canvas = document.getElementById('captureCanvas');
        const context = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);

        return canvas.toDataURL('image/jpeg', 0.85);
    }

    async analyzeEmotion() {
        const message = document.getElementById('cameraMessage');
        message.textContent = 'Analyzing emotion...';

        try {
            const imageData = this.captureImage();
            const base64Image = imageData.split(',')[1];

            console.log('Sending emotion scan request...');

            // Try real API first, fallback to mock if unavailable
            let result;
            try {
                const response = await fetch('http://localhost:5000/emotion-scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: base64Image, user_id: this.userId }),
                    timeout: 5000,
                });

                if (response.ok) {
                    result = await response.json();
                    console.log('Emotion analysis result:', result);
                } else {
                    throw new Error(`API returned ${response.status}`);
                }
            } catch (apiError) {
                console.warn('Emotion API unavailable, using mock response:', apiError.message);
                result = this.getMockEmotionResult();
            }

            this.currentEmotion = result.emotion;
            this.currentConfidence = result.confidence;

            this.showEmotionResult(result);
            this.renderTasks();
            this.updateEmotionBadge();
        } catch (error) {
            message.textContent = `Error: ${error.message}`;
            message.style.color = '#dc2626';
            console.error('Emotion analysis error:', error);
        }
    }

    getMockEmotionResult() {
        const emotions = [
            { emotion: 'focused', confidence: 0.85 },
            { emotion: 'stressed', confidence: 0.72 },
            { emotion: 'neutral', confidence: 0.88 },
        ];
        const random = emotions[Math.floor(Math.random() * emotions.length)];
        console.log('Using mock emotion result:', random);
        return random;
    }

    showEmotionResult(result) {
        this.closeCamera();

        const emotionIcons = {
            focused: '🎯',
            stressed: '😰',
            neutral: '😐',
        };

        const emotionMessages = {
            focused:
                'You\'re in focus mode! Tackle your high-priority tasks now for maximum impact.',
            stressed:
                'You\'re feeling stressed. Start with easy tasks to build momentum and confidence.',
            neutral:
                'You\'re in a neutral state. You can take on any type of task.',
        };

        document.getElementById('resultIcon').textContent = emotionIcons[result.emotion];
        document.getElementById('resultEmotion').textContent = result.emotion;
        document.getElementById('resultConfidenceValue').textContent = Math.round(
            result.confidence * 100
        );
        document.getElementById('resultMessage').textContent = emotionMessages[result.emotion];

        document.getElementById('resultModal').classList.add('active');
        document.getElementById('modalBackdrop').classList.add('active');
    }

    closeEmotionResult() {
        document.getElementById('resultModal').classList.remove('active');
        document.getElementById('modalBackdrop').classList.remove('active');
    }

    updateEmotionBadge() {
        if (!this.currentEmotion) return;

        const emotionIcons = { focused: '🎯', stressed: '😰', neutral: '😐' };
        const container = document.getElementById('emotionBadgeContainer');

        document.getElementById('emotionIcon').textContent = emotionIcons[this.currentEmotion];
        document.getElementById('emotionLabel').textContent = this.capitalizeFirst(
            this.currentEmotion
        );
        document.getElementById('emotionConfidenceLabel').textContent = `${Math.round(
            this.currentConfidence * 100
        )}% confidence`;

        container.style.display = 'flex';
    }

    clearEmotion() {
        this.currentEmotion = null;
        this.currentConfidence = null;
        document.getElementById('emotionBadgeContainer').style.display = 'none';
        this.renderTasks();
    }

    /* ============================================
       Event Listeners
       ============================================ */

    setupEventListeners() {
        // Add task
        const taskInput = document.getElementById('taskInput');
        const addBtn = document.getElementById('addTaskBtn');

        addBtn.addEventListener('click', () => {
            const text = taskInput.value;
            if (text.trim()) {
                this.addTask(text);
                taskInput.value = '';
                taskInput.focus();
            }
        });

        taskInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addBtn.click();
            }
        });

        // Camera FAB
        document.getElementById('emotionScanBtn').addEventListener('click', () => {
            this.openCamera();
        });

        // Camera modal controls
        document.getElementById('closeCamera').addEventListener('click', () => {
            this.closeCamera();
        });

        document.getElementById('cancelCamera').addEventListener('click', () => {
            this.closeCamera();
        });

        document.getElementById('captureImage').addEventListener('click', () => {
            this.analyzeEmotion();
        });

        // Result modal
        document.getElementById('closeResult').addEventListener('click', () => {
            this.closeEmotionResult();
        });

        document.getElementById('closeResultBtn').addEventListener('click', () => {
            this.closeEmotionResult();
        });

        // Clear emotion badge
        document.getElementById('clearEmotionBtn').addEventListener('click', () => {
            this.clearEmotion();
        });

        // Backdrop click
        document.getElementById('modalBackdrop').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                const cameraModal = document.getElementById('cameraModal');
                const resultModal = document.getElementById('resultModal');

                if (cameraModal.classList.contains('active')) {
                    this.closeCamera();
                } else if (resultModal.classList.contains('active')) {
                    this.closeEmotionResult();
                }
            }
        });

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const cameraModal = document.getElementById('cameraModal');
                const resultModal = document.getElementById('resultModal');

                if (cameraModal.classList.contains('active')) {
                    this.closeCamera();
                } else if (resultModal.classList.contains('active')) {
                    this.closeEmotionResult();
                }
            }
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            if (confirm('Are you sure you want to logout?')) {
                localStorage.removeItem('isLoggedIn');
                localStorage.removeItem('userName');
                window.location.href = 'login.html';
            }
        });
    }

    cleanup() {
        this.stopCamera();
    }
}

/* ============================================
   Initialization
   ============================================ */

let dashboard;

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - Initializing dashboard...');
    dashboard = new TaskDashboard();
});

window.addEventListener('beforeunload', () => {
    if (dashboard) {
        dashboard.cleanup();
    }
});
