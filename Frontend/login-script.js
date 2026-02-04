document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorMessage = document.getElementById('errorMessage');
    
    // Clear previous error
    errorMessage.classList.remove('show');
    
    // Basic validation
    if (!username || !password) {
        showError('Please fill in all fields');
        return;
    }
    
    if (password.length < 6) {
        showError('Password must be at least 6 characters');
        return;
    }
    
    // Here you would typically send login request to your backend
    // Example:
    // fetch('/api/login', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify({
    //         username: username,
    //         password: password
    //     })
    // })
    // .then(response => response.json())
    // .then(data => {
    //     if (data.success) {
    //         // Redirect to main page
    //         window.location.href = 'index.html';
    //     } else {
    //         showError(data.message || 'Login failed');
    //     }
    // })
    // .catch(error => {
    //     showError('Error: ' + error.message);
    // });
    
    // For now, just redirect to main page (demo)
    console.log('Login attempt:', { username });
    alert('Login successful! (Demo mode)');
    window.location.href = 'index.html';
});

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
    errorMessage.classList.add('show');
}

// Add click handlers for navigation links
document.querySelector('.forgot-password').addEventListener('click', function(e) {
    e.preventDefault();
    window.location.href = 'forgot-password.html';
});

document.querySelector('.signup').addEventListener('click', function(e) {
    e.preventDefault();
    window.location.href = 'signup.html';
});
