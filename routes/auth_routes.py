"""Auth Routes — now using SQLite"""
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, make_response
from utils.sql_db import db_insert, db_get_by_id, db_update, get_user_by_email, get_user_by_phone
from utils.auth_helper import hash_password, verify_password, create_token, get_current_user
from utils.cache import cache

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login_page():
    if get_current_user(): return redirect(url_for('main.home'))
    return render_template('login.html', page='login')


@auth_bp.route('/register')
def register_page():
    if get_current_user(): return redirect(url_for('main.home'))
    return render_template('login.html', page='register')


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data: return jsonify({'error':'No data provided'}), 400

    name  = data.get('name','').strip()
    email = data.get('email','').strip().lower()
    pwd   = data.get('password','')
    phone = data.get('phone','').strip()
    otp_v = data.get('otp_verified', False)

    if not name:          return jsonify({'error':'Name is required'}), 400
    if not email:         return jsonify({'error':'Email is required'}), 400
    if len(pwd) < 6:      return jsonify({'error':'Password must be at least 6 characters'}), 400
    if '@' not in email:  return jsonify({'error':'Invalid email address'}), 400

    if get_user_by_email(email):
        return jsonify({'error':'Email already registered'}), 409

    user = db_insert('users', {
        'name': name, 'email': email, 'password': hash_password(pwd),
        'phone': phone, 'avatar': '', 'avatar_url': '', 'bio': '',
        'otp_verified': otp_v
    })
    if not user: return jsonify({'error':'Registration failed'}), 500

    session['user_id'] = user['id']
    session.permanent = True
    token = create_token(user['id'], user['email'])
    resp  = make_response(jsonify({'success':True,'user':{'id':user['id'],'name':user['name'],'email':user['email']},'token':token}))
    resp.set_cookie('auth_token', token, max_age=86400, httponly=True, samesite='Lax')
    return resp, 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data  = request.get_json()
    if not data: return jsonify({'error':'No data provided'}), 400

    email = data.get('email','').strip().lower()
    phone = data.get('phone','').strip()
    pwd   = data.get('password','')

    user = None
    if email:   user = get_user_by_email(email)
    elif phone: user = get_user_by_phone(phone)

    if not user:
        return jsonify({'error':'Account not found. Please register first.'}), 401
    if not verify_password(pwd, user.get('password','')):
        return jsonify({'error':'Incorrect password'}), 401

    session['user_id'] = user['id']
    session.permanent  = True
    token = create_token(user['id'], user['email'])
    resp  = make_response(jsonify({'success':True,'user':{'id':user['id'],'name':user['name'],'email':user['email']},'redirect':'/'}))
    resp.set_cookie('auth_token', token, max_age=86400, httponly=True, samesite='Lax')
    return resp


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    resp = make_response(jsonify({'success':True}))
    resp.delete_cookie('auth_token')
    return resp


@auth_bp.route('/logout')
def logout_page():
    session.clear()
    resp = make_response(redirect(url_for('main.index')))
    resp.delete_cookie('auth_token')
    return resp


@auth_bp.route('/api/auth/me', methods=['GET'])
def me():
    user = get_current_user()
    if not user: return jsonify({'authenticated':False}), 401
    return jsonify({'authenticated':True,'user':{'id':user['id'],'name':user['name'],'email':user['email']}})

@auth_bp.route('/api/auth/login-email', methods=['POST'])
def login_by_email():
    """
    Simple login — user enters email, if account exists they are logged in.
    No password or OTP needed for login.
    """
    data  = request.get_json()
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'error': 'Email address is required'}), 400
    if '@' not in email:
        return jsonify({'error': 'Please enter a valid email address'}), 400

    # Check if user exists
    user = get_user_by_email(email)
    if not user:
        return jsonify({
            'error': 'No account found with this email. Please register first.'
        }), 404

    # Log them in directly
    session['user_id'] = user['id']
    session.permanent  = True
    token = create_token(user['id'], user['email'])

    resp = make_response(jsonify({
        'success': True,
        'user':    {
            'id':    user['id'],
            'name':  user['name'],
            'email': user['email']
        },
        'redirect': '/home'
    }))
    resp.set_cookie('auth_token', token, max_age=86400*30, httponly=True, samesite='Lax')
    return resp
