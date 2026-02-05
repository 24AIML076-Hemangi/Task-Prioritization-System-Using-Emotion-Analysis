document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    
    // Basic validation
    if (!username || !password) {
        console.warn('Empty fields provided');
        return;
    }
    
    if (password.length < 6) {
        console.warn('Password too short');
        return;
    }
    
    // For now, just redirect to dashboard (demo)
    console.log('Login attempt:', { username });
    localStorage.setItem('userName', username);
    localStorage.setItem('isLoggedIn', 'true');
    window.location.href = 'dashboard.html';
});


function showError(message) {
    console.error('Login error:', message);
}
