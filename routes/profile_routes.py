from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from utils.sql_db import get_db, db_get_by_id, db_update
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
def profile_page():
    """Profile page"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    
    # Get user from database
    user = db_get_by_id('users', user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get saved places (if you have this functionality)
    saved_places = []
    
    return render_template('profile.html', 
                         user=user,
                         saved_places=saved_places,
                         reviews_count=0,
                         states_visited=0)


@profile_bp.route('/api/profile/avatar', methods=['POST'])
def upload_avatar():
    """Upload profile avatar"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Save file
    filename = secure_filename(f"user_{session['user_id']}_{file.filename}")
    upload_folder = 'static/images/avatars'
    
    # Create folder if doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Update user in database
    avatar_url = f'/static/images/avatars/{filename}'
    db_update('users', session['user_id'], {'avatar_url': avatar_url})
    
    return jsonify({'success': True, 'avatar_url': avatar_url}), 200


@profile_bp.route('/api/profile/bio', methods=['POST'])
def update_bio():
    """Update user bio"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    bio = data.get('bio', '').strip()
    
    # Update user in database
    db_update('users', session['user_id'], {'bio': bio})
    
    return jsonify({'success': True}), 200

@profile_bp.route('/saved')
def saved_places():
    """Saved places page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = db_get_by_id('users', user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    # Get saved places
    # Assuming you have a saved_places relationship or field
    from utils.sql_db import db_get_all
    
    saved_places = []
    # If you have a saved_places table or user.saved_places field, fetch them here
    # For now, returning empty list
    
    return render_template('saved_places.html', 
                         user=user,
                         saved_places=saved_places)


@profile_bp.route('/settings')
def settings_page():
    """Settings page"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    user = db_get_by_id('users', user_id)
    
    if not user:
        return redirect(url_for('auth.login'))
    
    return render_template('settings.html', user=user)

@profile_bp.route('/api/profile', methods=['PUT'])
def update_profile():
    """Update profile info (name, bio, etc.)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.get_json()
    updates = {}
    
    if 'name' in data:
        updates['name'] = data['name'].strip()
    
    if 'bio' in data:
        updates['bio'] = data['bio'].strip()
    
    if updates:
        db_update('users', session['user_id'], updates)
    
    return jsonify({'success': True}), 200