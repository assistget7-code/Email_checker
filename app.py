from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import sqlite3
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here")
CORS(app)  # Allow frontend to call this API

# ============================================
# DATABASE SETUP
# ============================================

def init_db():
    """Create database tables if they don't exist"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Licenses table (for the license system)
    c.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'active',
            expires_at TIMESTAMP,
            owner_email TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================
# API ROUTES
# ============================================

@app.route('/api/login', methods=['POST'])
def login():
    """Verify email and password"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password_hash = data.get('pass', '')  # Already hashed by frontend
    
    if not email or not password_hash:
        return jsonify({"message": "Email and password required"}), 400
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Check if user exists
    c.execute('SELECT password_hash, full_name FROM users WHERE email = ?', (email,))
    result = c.fetchone()
    conn.close()
    
    if result:
        stored_hash = result[0]
        full_name = result[1]
        
        # Compare hashes
        if stored_hash == password_hash:
            return jsonify({
                "message": "Login successful",
                "user": {"email": email, "full_name": full_name}
            })
    
    # Generic error message for security (don't reveal if email exists)
    return jsonify({"message": "That password doesn't look right"}), 401

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '')
    
    if not email or not password:
        return jsonify({"message": "Email and password required"}), 400
    
    password_hash = hash_password(password)
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)',
                  (email, password_hash, full_name))
        conn.commit()
        return jsonify({"message": "User registered successfully"})
    except sqlite3.IntegrityError:
        return jsonify({"message": "Email already exists"}), 400
    finally:
        conn.close()

@app.route('/api/verify-license/<license_key>', methods=['GET'])
def verify_license(license_key):
    """Check if a license key is valid"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT status, expires_at, owner_email FROM licenses WHERE license_key = ?', (license_key,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"status": "invalid", "message": "License not found"}), 404
    
    status = result[0]
    expires_at = result[1]
    
    if status == 'expired':
        return jsonify({"status": "expired", "expiresAt": expires_at})
    
    if expires_at and datetime.now() > datetime.fromisoformat(expires_at):
        return jsonify({"status": "expired", "expiresAt": expires_at})
    
    return jsonify({"status": "active", "expiresAt": expires_at})

@app.route('/api/generate-license', methods=['POST'])
def generate_license():
    """Generate a new license key"""
    data = request.get_json()
    owner_email = data.get('owner_email', '')
    days_valid = data.get('days_valid', 30)
    
    import uuid
    license_key = str(uuid.uuid4())[:8].upper()
    expires_at = (datetime.now() + timedelta(days=days_valid)).isoformat()
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT INTO licenses (license_key, status, expires_at, owner_email) VALUES (?, ?, ?, ?)',
              (license_key, 'active', expires_at, owner_email))
    conn.commit()
    conn.close()
    
    return jsonify({
        "success": True,
        "license_key": license_key,
        "expires_at": expires_at
    })

@app.route('/api/users', methods=['GET'])
def list_users():
    """List all users (for testing)"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT email, full_name, created_at FROM users')
    users = c.fetchall()
    conn.close()
    
    return jsonify({"users": [{"email": u[0], "full_name": u[1], "created_at": u[2]} for u in users]})

if __name__ == '__main__':
    init_db()
    # Add a test user for demo
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)',
                  ('demo@example.com', hash_password('demo123'), 'Demo User'))
        conn.commit()
        print("✅ Demo user created: demo@example.com / demo123")
    except sqlite3.IntegrityError:
        pass  # User already exists
    conn.close()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
