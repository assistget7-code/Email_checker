// email.js - Complete login logic

// SHA-256 hashing function
async function sha256(message) {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Show toast notification
function showToast(type, message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';
    
    // Auto-hide after 5 seconds
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => {
        toast.style.display = 'none';
    }, 5000);
}

// Main login function
async function onSignin() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('loginBtn');
    
    // Validate inputs
    if (!email || !password) {
        showToast('error', 'Please fill in all fields.');
        return;
    }
    
    // Disable button and show loading
    loginBtn.disabled = true;
    loginBtn.textContent = 'Checking...';
    
    try {
        // Hash the password
        const hashedPassword = await sha256(password);
        
        // Send to backend
        const response = await fetch(ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email: email, 
                pass: hashedPassword 
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.message === 'Login successful') {
            showToast('success', '✅ Login successful! Redirecting...');
            
            // Redirect to dashboard after 1 second
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        } else {
            showToast('error', data.message || 'That password doesn\'t look right.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('error', 'Network error. Please try again.');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Sign in';
    }
}

// Registration function
async function onRegister() {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const loginBtn = document.getElementById('loginBtn');
    
    if (!email || !password) {
        showToast('error', 'Please fill in all fields.');
        return;
    }
    
    loginBtn.disabled = true;
    loginBtn.textContent = 'Creating...';
    
    try {
        const hashedPassword = await sha256(password);
        
        const response = await fetch(ENDPOINT.replace('/login', '/register'), {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email: email, 
                password: password,  // Send plain for registration (backend will hash)
                full_name: email.split('@')[0]
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('success', '✅ Account created! You can now sign in.');
        } else {
            showToast('error', data.message || 'Registration failed.');
        }
    } catch (error) {
        showToast('error', 'Network error. Please try again.');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Sign in';
    }
}

// Toggle between login and register
function showRegister() {
    const form = document.getElementById('loginForm');
    const btn = document.getElementById('loginBtn');
    const title = document.querySelector('h2');
    
    if (btn.textContent === 'Sign in') {
        title.textContent = 'Create Account';
        btn.textContent = 'Create Account';
        btn.onclick = onRegister;
        document.querySelector('.text-center a').textContent = '← Back to sign in';
        document.querySelector('.text-center a').onclick = function(e) {
            e.preventDefault();
            location.reload();
        };
        // Remove the "Forgot password" text
        document.querySelector('.text-center .mx-2').style.display = 'none';
    }
}

// Event listener for login form
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const btn = document.getElementById('loginBtn');
            if (btn.textContent === 'Create Account') {
                onRegister();
            } else {
                onSignin();
            }
        });
    }
});
