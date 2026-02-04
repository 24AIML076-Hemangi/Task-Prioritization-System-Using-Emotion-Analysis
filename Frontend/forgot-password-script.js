// State management
const state = {
    currentStep: 'email', // email -> code -> password -> success
    email: '',
    resetToken: '',
    resetCode: '',
    isResending: false
};

// DOM Elements
const emailForm = document.getElementById('emailForm');
const codeForm = document.getElementById('codeForm');
const passwordForm = document.getElementById('passwordForm');
const resendBtn = document.getElementById('resendBtn');
const newPasswordInput = document.getElementById('newPassword');

// Form Steps
const emailStep = document.getElementById('emailStep');
const codeStep = document.getElementById('codeStep');
const passwordStep = document.getElementById('passwordStep');
const successStep = document.getElementById('successStep');
const loading = document.getElementById('loading');

// API Base URL - adjust based on your backend
const API_BASE_URL = 'http://localhost:5000/api';

// Initialize event listeners
function initializeEventListeners() {
    emailForm.addEventListener('submit', handleEmailSubmit);
    codeForm.addEventListener('submit', handleCodeSubmit);
    passwordForm.addEventListener('submit', handlePasswordSubmit);
    resendBtn.addEventListener('click', handleResendCode);
    newPasswordInput.addEventListener('input', validatePasswordRequirements);
}

// Step 1: Email Submission
async function handleEmailSubmit(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const emailError = document.getElementById('emailError');

    // Clear previous errors
    emailError.textContent = '';

    // Validate email
    if (!isValidEmail(email)) {
        emailError.textContent = 'Please enter a valid email address';
        return;
    }

    try {
        showLoading(true);
        
        // Call backend to send reset email
        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (!response.ok) {
            emailError.textContent = data.message || 'Failed to send reset email';
            return;
        }

        // Store email for later use
        state.email = email;
        state.resetToken = data.resetToken; // Store token if provided

        // Move to code verification step
        goToStep('code');
        showNotification('Reset code sent to your email', 'success');

    } catch (error) {
        console.error('Error:', error);
        emailError.textContent = 'Network error. Please try again.';
    } finally {
        showLoading(false);
    }
}

// Step 2: Code Verification
async function handleCodeSubmit(e) {
    e.preventDefault();

    const code = document.getElementById('resetCode').value.trim();
    const codeError = document.getElementById('codeError');

    // Clear previous errors
    codeError.textContent = '';

    // Validate code
    if (code.length !== 6 || isNaN(code)) {
        codeError.textContent = 'Please enter a valid 6-digit code';
        return;
    }

    try {
        showLoading(true);

        // Verify the code with backend
        const response = await fetch(`${API_BASE_URL}/auth/verify-reset-code`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: state.email,
                code: code
            })
        });

        const data = await response.json();

        if (!response.ok) {
            codeError.textContent = data.message || 'Invalid code. Please try again.';
            return;
        }

        // Store the verified token
        state.resetCode = code;
        state.resetToken = data.resetToken;

        // Move to password reset step
        goToStep('password');
        showNotification('Code verified successfully', 'success');

    } catch (error) {
        console.error('Error:', error);
        codeError.textContent = 'Network error. Please try again.';
    } finally {
        showLoading(false);
    }
}

// Step 3: Password Reset
async function handlePasswordSubmit(e) {
    e.preventDefault();

    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const passwordError = document.getElementById('passwordError');
    const confirmError = document.getElementById('confirmError');

    // Clear previous errors
    passwordError.textContent = '';
    confirmError.textContent = '';

    // Validate passwords
    if (!validatePassword(newPassword)) {
        passwordError.textContent = 'Password does not meet requirements';
        return;
    }

    if (newPassword !== confirmPassword) {
        confirmError.textContent = 'Passwords do not match';
        return;
    }

    try {
        showLoading(true);

        // Send password reset request to backend
        const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: state.email,
                code: state.resetCode,
                resetToken: state.resetToken,
                newPassword: newPassword
            })
        });

        const data = await response.json();

        if (!response.ok) {
            passwordError.textContent = data.message || 'Failed to reset password';
            return;
        }

        // Show success message
        goToStep('success');

    } catch (error) {
        console.error('Error:', error);
        passwordError.textContent = 'Network error. Please try again.';
    } finally {
        showLoading(false);
    }
}

// Resend reset code
async function handleResendCode() {
    if (state.isResending) return;

    try {
        state.isResending = true;
        resendBtn.disabled = true;
        resendBtn.textContent = 'Sending...';

        const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: state.email })
        });

        if (response.ok) {
            showNotification('Code resent to your email', 'success');
            
            // Reset timer
            let seconds = 60;
            const timer = setInterval(() => {
                seconds--;
                resendBtn.textContent = `Resend (${seconds}s)`;
                if (seconds <= 0) {
                    clearInterval(timer);
                    resendBtn.disabled = false;
                    resendBtn.textContent = 'Resend';
                    state.isResending = false;
                }
            }, 1000);
        } else {
            showNotification('Failed to resend code', 'error');
            resendBtn.disabled = false;
            resendBtn.textContent = 'Resend';
            state.isResending = false;
        }

    } catch (error) {
        console.error('Error:', error);
        showNotification('Network error', 'error');
        resendBtn.disabled = false;
        resendBtn.textContent = 'Resend';
        state.isResending = false;
    }
}

// Validate password requirements
function validatePasswordRequirements() {
    const password = newPasswordInput.value;

    const requirements = {
        length: password.length >= 8,
        upper: /[A-Z]/.test(password),
        lower: /[a-z]/.test(password),
        number: /\d/.test(password)
    };

    updateRequirementUI('req-length', requirements.length);
    updateRequirementUI('req-upper', requirements.upper);
    updateRequirementUI('req-lower', requirements.lower);
    updateRequirementUI('req-number', requirements.number);

    return Object.values(requirements).every(req => req);
}

// Update requirement UI
function updateRequirementUI(elementId, isMet) {
    const element = document.getElementById(elementId);
    if (isMet) {
        element.classList.add('met');
    } else {
        element.classList.remove('met');
    }
}

// Validate password
function validatePassword(password) {
    const requirements = {
        length: password.length >= 8,
        upper: /[A-Z]/.test(password),
        lower: /[a-z]/.test(password),
        number: /\d/.test(password)
    };

    return Object.values(requirements).every(req => req);
}

// Validate email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Navigate to a specific step
function goToStep(step) {
    // Hide all steps
    emailStep.classList.remove('active');
    codeStep.classList.remove('active');
    passwordStep.classList.remove('active');
    successStep.classList.remove('active');

    // Show the requested step
    switch(step) {
        case 'email':
            emailStep.classList.add('active');
            break;
        case 'code':
            codeStep.classList.add('active');
            document.getElementById('resetCode').focus();
            break;
        case 'password':
            passwordStep.classList.add('active');
            newPasswordInput.focus();
            break;
        case 'success':
            successStep.classList.add('active');
            break;
    }

    state.currentStep = step;
}

// Show/hide loading state
function showLoading(show) {
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

// Show notification message
function showNotification(message, type = 'info') {
    // Create a simple notification (you can enhance this with a toast library)
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Optional: You can add a visual notification here
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeEventListeners);
