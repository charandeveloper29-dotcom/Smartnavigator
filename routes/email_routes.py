"""
Email OTP Routes — Gmail SMTP verification
POST /api/email/send-otp    → generate & send OTP to email
POST /api/email/verify-otp  → verify OTP, create account, auto-login
"""
import secrets
from flask import Blueprint, request, jsonify, session, make_response
from utils.email_otp import store_email_otp, check_email_otp, send_otp_email, generate_otp
from utils.sql_db import db_insert, get_user_by_email
from utils.auth_helper import hash_password, create_token

email_bp = Blueprint('email', __name__)


@email_bp.route('/api/email/send-otp', methods=['POST'])
def send_otp():
    data    = request.get_json() or {}
    email   = (data.get('email') or '').strip().lower()
    name    = (data.get('name')  or '').strip()
    purpose = data.get('purpose', 'register')

    if not email or '@' not in email:
        return jsonify({'error': 'Valid email address is required'}), 400

    if purpose == 'register' and get_user_by_email(email):
        return jsonify({'error': 'This email is already registered. Please sign in.'}), 409

    otp = generate_otp()
    store_email_otp(email, otp, purpose=purpose)

    success, message = send_otp_email(email, otp, user_name=name)
    if not success:
        return jsonify({'error': message}), 500

    return jsonify({
        'success': True,
        'message': f'OTP sent to {email}',
        'email':   email
    })


@email_bp.route('/api/email/verify-otp', methods=['POST'])
def verify_otp():
    data    = request.get_json() or {}
    email   = (data.get('email') or '').strip().lower()
    otp     = (data.get('otp')   or '').strip()
    name    = (data.get('name')  or '').strip()
    purpose = data.get('purpose', 'register')

    if not email or not otp:
        return jsonify({'error': 'Email and OTP are required'}), 400
    if not name and purpose == 'register':
        return jsonify({'error': 'Name is required'}), 400

    result = check_email_otp(email, otp, purpose=purpose)
    if not result['valid']:
        return jsonify({'error': result.get('error', 'OTP verification failed')}), 400

    if purpose == 'register':
        if get_user_by_email(email):
            return jsonify({'error': 'Email already registered. Please sign in.'}), 409

        user = db_insert('users', {
            'name':         name,
            'email':        email,
            'phone':        '',
            'password':     hash_password(secrets.token_urlsafe(16)),
            'avatar':       '',
            'avatar_url':   '',
            'bio':          '',
            'otp_verified': True,
        })

        if not user:
            return jsonify({'error': 'Account creation failed. Please try again.'}), 500

    else:
        user = get_user_by_email(email)
        if not user:
            return jsonify({'error': 'No account found for this email.'}), 404

    session['user_id'] = user['id']
    session.permanent  = True
    token = create_token(user['id'], user['email'])

    resp = make_response(jsonify({
        'success':  True,
        'message':  f'Welcome to Smart Navigator, {name or user.get("name", "")}!',
        'user':     {'id': user['id'], 'name': user['name'], 'email': user['email']},
        'redirect': '/home'
    }))
    resp.set_cookie('auth_token', token, max_age=86400 * 30, httponly=True, samesite='Lax')
    return resp, 201