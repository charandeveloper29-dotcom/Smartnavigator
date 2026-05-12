"""
OTP Routes — Real SMS/Email OTP endpoints
"""
from flask import Blueprint, request, jsonify, session, make_response
from utils.otp_service import send_otp, verify_otp
from utils.sql_db import (db_insert, get_user_by_email, get_user_by_phone,
                           db_get_by_id, db_update, db_execute)
from utils.auth_helper import hash_password, create_token, verify_password

otp_bp = Blueprint('otp', __name__)


# ── STEP 1: Send OTP ─────────────────────────────────────
@otp_bp.route('/api/otp/send', methods=['POST'])
def send_otp_api():
    """
    Send real OTP to phone or email.
    Body: { "identifier": "9876543210" or "user@email.com",
            "purpose": "register" | "login",
            "name": "User Name" (optional) }
    """
    data       = request.get_json()
    identifier = (data.get('identifier') or '').strip()
    purpose    = data.get('purpose', 'register')
    name       = data.get('name', '')

    if not identifier:
        return jsonify({'error': 'Phone number or email is required'}), 400

    is_email = '@' in identifier

    # Validate phone
    if not is_email:
        clean = ''.join(filter(str.isdigit, identifier))
        if len(clean) != 10:
            return jsonify({'error': 'Enter a valid 10-digit mobile number'}), 400
        identifier = clean

    # For login: check if user exists
    if purpose == 'login':
        user = get_user_by_email(identifier) if is_email else get_user_by_phone(identifier)
        if not user:
            return jsonify({'error': 'No account found. Please register first.'}), 404

    # For register: check if already registered
    if purpose == 'register':
        existing = get_user_by_email(identifier) if is_email else get_user_by_phone(identifier)
        if existing:
            return jsonify({'error': 'This account already exists. Please login.'}), 409

    # Send OTP
    result = send_otp(identifier, purpose=purpose, user_name=name)

    if not result['success']:
        return jsonify({'error': result['message']}), 500

    response = {
        'success':    True,
        'message':    result['message'],
        'method':     result['method'],
        'masked':     result.get('masked', identifier[:3] + '****'),
        'expires_in': 10,
    }
    return jsonify(response)


# ── STEP 2: Verify OTP & Register ────────────────────────
@otp_bp.route('/api/otp/verify-register', methods=['POST'])
def verify_and_register():
    """
    Verify OTP and create new user account.
    Body: { "identifier": "9876543210", "otp": "123456",
            "name": "Arjun", "email": "a@b.com" (if phone registration) }
    """
    data       = request.get_json()
    identifier = (data.get('identifier') or '').strip()
    otp_code   = (data.get('otp') or '').strip()
    name       = (data.get('name') or '').strip()

    if not identifier or not otp_code:
        return jsonify({'error': 'Identifier and OTP are required'}), 400
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Verify OTP
    result = verify_otp(identifier, otp_code, purpose='register')
    if not result['valid']:
        return jsonify({'error': result['message']}), 400

    # Create user account
    is_email = '@' in identifier
    if is_email:
        email = identifier
        phone = data.get('phone', '').strip()
    else:
        phone = identifier
        email = data.get('email', '').strip()
        if not email:
            # Generate a placeholder email
            email = f'user_{phone}@smartnav.app'

    # Check again just in case
    existing = get_user_by_email(email)
    if existing:
        return jsonify({'error': 'Email already registered. Please login.'}), 409

    # Generate a random secure password for OTP-based accounts
    import secrets
    auto_pwd = secrets.token_urlsafe(16)

    user = db_insert('users', {
        'name':         name,
        'email':        email,
        'phone':        phone,
        'password':     hash_password(auto_pwd),
        'otp_verified': True,
        'avatar':       '',
        'avatar_url':   '',
        'bio':          '',
    })

    if not user:
        return jsonify({'error': 'Account creation failed. Please try again.'}), 500

    # Auto-login
    session['user_id'] = user['id']
    session.permanent  = True
    token = create_token(user['id'], user['email'])

    resp = make_response(jsonify({
        'success': True,
        'message': f'Welcome to Smart Navigator, {name}!',
        'user':    {'id': user['id'], 'name': user['name'], 'email': user['email']},
        'redirect': '/home'
    }))
    resp.set_cookie('auth_token', token, max_age=86400*30, httponly=True, samesite='Lax')
    return resp, 201


# ── STEP 3: Verify OTP & Login ───────────────────────────
@otp_bp.route('/api/otp/verify-login', methods=['POST'])
def verify_and_login():
    """
    Verify OTP and log in existing user.
    Body: { "identifier": "9876543210", "otp": "123456" }
    """
    data       = request.get_json()
    identifier = (data.get('identifier') or '').strip()
    otp_code   = (data.get('otp') or '').strip()

    if not identifier or not otp_code:
        return jsonify({'error': 'Identifier and OTP are required'}), 400

    # Verify OTP
    result = verify_otp(identifier, otp_code, purpose='login')
    if not result['valid']:
        return jsonify({'error': result['message']}), 400

    # Get user
    is_email = '@' in identifier
    user = get_user_by_email(identifier) if is_email else get_user_by_phone(identifier)
    if not user:
        return jsonify({'error': 'Account not found'}), 404

    # Login
    session['user_id'] = user['id']
    session.permanent  = True
    token = create_token(user['id'], user['email'])

    resp = make_response(jsonify({
        'success': True,
        'message': f'Welcome back, {user["name"]}!',
        'user':    {'id': user['id'], 'name': user['name'], 'email': user['email']},
        'redirect': '/home'
    }))
    resp.set_cookie('auth_token', token, max_age=86400*30, httponly=True, samesite='Lax')
    return resp


# ── Password-based login (fallback) ──────────────────────
@otp_bp.route('/api/otp/login-password', methods=['POST'])
def login_with_password():
    """Login with email/phone + password (for users who set a password)."""
    data       = request.get_json()
    identifier = (data.get('identifier') or '').strip().lower()
    pwd        = data.get('password', '')

    is_email = '@' in identifier
    user = get_user_by_email(identifier) if is_email else get_user_by_phone(identifier)

    if not user:
        return jsonify({'error': 'Account not found. Please register.'}), 401
    if not verify_password(pwd, user.get('password', '')):
        return jsonify({'error': 'Incorrect password'}), 401

    session['user_id'] = user['id']
    session.permanent  = True
    token = create_token(user['id'], user['email'])

    resp = make_response(jsonify({
        'success': True,
        'user':    {'id': user['id'], 'name': user['name'], 'email': user['email']},
        'redirect': '/home'
    }))
    resp.set_cookie('auth_token', token, max_age=86400*30, httponly=True, samesite='Lax')
    return resp


# ── Resend OTP ────────────────────────────────────────────
@otp_bp.route('/api/otp/resend', methods=['POST'])
def resend_otp():
    """Resend a fresh OTP."""
    data       = request.get_json()
    identifier = (data.get('identifier') or '').strip()
    purpose    = data.get('purpose', 'register')
    name       = data.get('name', '')

    if not identifier:
        return jsonify({'error': 'Identifier required'}), 400

    result = send_otp(identifier, purpose=purpose, user_name=name)
    if not result['success']:
        return jsonify({'error': result['message']}), 500
    return jsonify({
        'success': True,
        'message': result['message'],
        'method':  result['method'],
        'masked':  result.get('masked', ''),
    })
