"""
Authentication Helper Module
Handles password hashing, JWT token creation/verification
"""

import hashlib
import hmac
import os
import time
import base64
import json
from functools import wraps
from flask import request, jsonify, session, redirect, url_for


SECRET_KEY = os.environ.get('SECRET_KEY', 'smart_navigator_secret_2024_change_in_prod')
JWT_EXPIRY = 86400  # 24 hours


# ─── Password Hashing ───────────────────────────────────────────────────────

def hash_password(password):
    """Hash password using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    dk_b64 = base64.b64encode(dk).decode('utf-8')
    return f"pbkdf2:sha256:260000${salt_b64}${dk_b64}"


def verify_password(password, password_hash):
    """Verify a plaintext password against a stored hash."""
    try:
        parts = password_hash.split('$')
        if len(parts) != 3:
            return False
        _, salt_b64, dk_b64 = parts
        salt = base64.b64decode(salt_b64)
        stored_dk = base64.b64decode(dk_b64)
        new_dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 260000)
        return hmac.compare_digest(stored_dk, new_dk)
    except Exception:
        return False


# ─── JWT Implementation ──────────────────────────────────────────────────────

def _b64_encode(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip('=')


def _b64_decode(data):
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return json.loads(base64.urlsafe_b64decode(data).decode())


def create_token(user_id, email):
    """Create a signed JWT token for a user."""
    header = _b64_encode({"alg": "HS256", "typ": "JWT"})
    payload = _b64_encode({
        "sub": user_id,
        "email": email,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY
    })
    signature_input = f"{header}.{payload}"
    sig = hmac.new(
        SECRET_KEY.encode(),
        signature_input.encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode().rstrip('=')
    return f"{header}.{payload}.{sig_b64}"


def verify_token(token):
    """
    Verify a JWT token.
    Returns the payload dict if valid, None if invalid/expired.
    """
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        # Verify signature
        signature_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            signature_input.encode(),
            hashlib.sha256
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')
        if not hmac.compare_digest(sig_b64, expected_b64):
            return None
        # Decode and verify expiry
        payload = _b64_decode(payload_b64)
        if payload.get('exp', 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_token_from_request():
    """Extract JWT token from Authorization header or cookie."""
    # Try Authorization header first
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    # Try cookie
    return request.cookies.get('auth_token')


def get_current_user():
    """Get current logged-in user from session or JWT."""
    # Try session first
    if 'user_id' in session:
        from utils.sql_db import db_get_by_id
        user = db_get_by_id('users', session['user_id'])
        if user:
            return user
    # Try JWT
    token = get_token_from_request()
    if token:
        payload = verify_token(token)
        if payload:
            from utils.sql_db import db_get_by_id
            return db_get_by_id('users', payload.get('sub'))
    return None


# ─── Decorators ──────────────────────────────────────────────────────────────

def login_required(f):
    """Decorator: requires user to be logged in for API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'code': 401}), 401
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated


def login_required_page(f):
    """Decorator: requires user to be logged in for page routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """Decorator: injects current user but doesn't require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated
