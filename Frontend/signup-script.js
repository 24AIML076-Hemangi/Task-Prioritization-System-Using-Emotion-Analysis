document.getElementById('signupForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const fullname = document.getElementById('fullname').value.trim();
    const email = document.getElementById('email').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const terms = document.getElementById('terms').checked;
    
    // Clear all previous errors
    clearAllErrors();
    
    let isValid = true;
    
    // Validate fullname
    if (!fullname) {
        showError('fullnameError', 'Full name is required');
        isValid = false;
    } else if (fullname.length < 2) {
        showError('fullnameError', 'Name must be at least 2 characters');
        isValid = false;
    } else {
        markSuccess('fullname');
    }
    
    // Validate email
    if (!email) {
        showError('emailError', 'Email is required');
        isValid = false;
    } else if (!isValidEmail(email)) {
        showError('emailError', 'Please enter a valid email');
        isValid = false;
    } else {
        markSuccess('email');
    }
    
    // Validate username
    if (!username) {
        showError('usernameError', 'Username is required');
        isValid = false;
    } else if (username.length < 3) {
        showError('usernameError', 'Username must be at least 3 characters');
        isValid = false;
    } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
        showError('usernameError', 'Username can only contain letters, numbers, and underscores');
        isValid = false;
    } else {
        markSuccess('username');
    }
    
    // Validate password
    if (!password) {
        showError('passwordError', 'Password is required');
        isValid = false;
    } else if (password.length < 8) {
        showError('passwordError', 'Password must be at least 8 characters');
        isValid = false;
    } else {
        markSuccess('password');
    }
    
    // Validate confirm password
    if (password !== confirmPassword) {
        showError('confirmPasswordError', 'Passwords do not match');
        isValid = false;
    } else if (confirmPassword) {
        markSuccess('confirmPassword');
    }
    
    // Validate terms
    if (!terms) {
        showError('termsError', 'You must agree to the terms');
        isValid = false;
    }
    
    if (isValid) {
        submitSignup(fullname, email, username, password);
    }
});

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function showError(elementId, message) {
    const errorElement = document.getElementById(elementId);
    const inputId = elementId.replace('Error', '');
    const inputElement = document.getElementById(inputId);
    
    if (inputElement) {
        inputElement.classList.add('error');
        inputElement.classList.remove('success');
    }
    
    errorElement.textContent = message;
    errorElement.classList.add('show');
}

function markSuccess(inputId) {
    const inputElement = document.getElementById(inputId);
    if (inputElement) {
        inputElement.classList.add('success');
        inputElement.classList.remove('error');
    }
}

function clearAllErrors() {
    const errorElements = document.querySelectorAll('.error-text');
    errorElements.forEach(el => {
        el.classList.remove('show');
        el.textContent = '';
    });
    
    const inputElements = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"]');
    inputElements.forEach(el => {
        el.classList.remove('error', 'success');
    });
}

function submitSignup(fullname, email, username, password) {
    const successMessage = document.getElementById('successMessage');
    const signupBtn = document.querySelector('.signup-btn');
    
    // Show loading state
    signupBtn.disabled = true;
    signupBtn.textContent = 'Creating Account...';
    
    // Here you would typically send signup request to your backend
    // Example:
    // fetch('/api/signup', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify({
    //         fullname: fullname,
    //         email: email,
    //         username: username,
    //         password: password
    //     })
    // })
    // .then(response => response.json())
    // .then(data => {
    //     if (data.success) {
    //         successMessage.textContent = 'Account created successfully! Redirecting to login...';
    //         successMessage.classList.add('show');
    //         setTimeout(() => {
    //             window.location.href = 'login.html';
    //         }, 2000);
    //     } else {
    //         showError('Account creation failed: ' + data.message);
    //         signupBtn.disabled = false;
    //         signupBtn.textContent = 'Create Account';
    //     }
    // })
    // .catch(error => {
    //     console.error('Error:', error);
    //     signupBtn.disabled = false;
    //     signupBtn.textContent = 'Create Account';
    // });
    
    // For demo purposes - simulate successful signup
    console.log('Signup data:', { fullname, email, username });
    
    setTimeout(() => {
        successMessage.textContent = 'Account created successfully! Redirecting to login...';
        successMessage.classList.add('show');
        
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
    }, 1000);
}

// Password strength indicator
document.getElementById('password').addEventListener('input', function() {
    const password = this.value;
    const strengthElement = document.getElementById('passwordStrength');
    
    if (!password) {
        strengthElement.textContent = '';
        return;
    }
    
    const strength = calculatePasswordStrength(password);
    
    if (strength < 2) {
        strengthElement.textContent = '⚠ Weak password';
        strengthElement.className = 'password-strength weak';
    } else if (strength < 4) {
        strengthElement.textContent = '➤ Fair password';
        strengthElement.className = 'password-strength fair';
    } else {
        strengthElement.textContent = '✓ Strong password';
        strengthElement.className = 'password-strength good';
    }
});

function calculatePasswordStrength(password) {
    let strength = 0;
    
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;
    
    return strength;
}
