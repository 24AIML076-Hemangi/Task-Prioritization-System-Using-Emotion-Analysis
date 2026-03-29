import { BASE_URL } from "./config.js";
const API_URL = `${BASE_URL}/api/auth`;

document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;

    if (!email || !password) {
        showError('Email and password are required');
        return;
    }

    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }

    const submitBtn = document.querySelector('.login-form button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in...';

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            showError(data.error || 'Login failed');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign in';
            return;
        }

        console.log('Login successful:', data.user);
        localStorage.setItem('isLoggedIn', 'true');
        localStorage.setItem('userEmail', data.user.email);
        localStorage.setItem('userId', data.user.id);
        localStorage.setItem('userName', data.user.email.split('@')[0]);
        localStorage.setItem('accessToken', data.access_token || '');
        localStorage.setItem('refreshToken', data.refresh_token || '');

        window.location.href = 'dashboard.html';

    } catch (error) {
        console.error('Login error:', error);
        showError('Server connection failed. Is the backend running?');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign in';
    }
});


function showError(message) {
    console.error('Login error:', message);
    alert(message);
}
