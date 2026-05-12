"""Reviews Routes — SQLite"""
from flask import Blueprint, request, jsonify
from utils.sql_db import db_find_by, db_insert, db_get_by_id, update_place_rating
from utils.auth_helper import get_current_user, login_required
from utils.cache import cache

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/api/places/<int:place_id>/reviews', methods=['GET'])
def get_reviews(place_id):
    reviews = db_find_by('reviews', 'place_id', place_id)
    reviews.sort(key=lambda r: r.get('created_at',''), reverse=True)
    return jsonify(reviews)


@reviews_bp.route('/api/places/<int:place_id>/reviews', methods=['POST'])
@login_required
def add_review(place_id):
    user = get_current_user()
    data = request.get_json()
    if not data: return jsonify({'error':'No data provided'}), 400

    rating  = data.get('rating')
    title   = data.get('title','').strip()
    content = data.get('content','').strip()

    if not rating or not isinstance(rating, int) or not 1 <= rating <= 5:
        return jsonify({'error':'Rating must be 1–5'}), 400
    if not content or len(content) < 10:
        return jsonify({'error':'Review must be at least 10 characters'}), 400
    if not title:
        return jsonify({'error':'Title is required'}), 400
    if not db_get_by_id('places', place_id):
        return jsonify({'error':'Place not found'}), 404

    # Check for duplicate review
    from utils.sql_db import db_execute
    existing = db_execute(
        "SELECT id FROM reviews WHERE place_id=? AND user_id=?",
        (place_id, user['id'])
    )
    if existing: return jsonify({'error':'You already reviewed this place'}), 409

    review = db_insert('reviews', {
        'place_id':  place_id, 'user_id': user['id'],
        'user_name': user['name'], 'rating': rating,
        'title': title, 'content': content, 'helpful_count': 0
    })
    if not review: return jsonify({'error':'Failed to save review'}), 500

    update_place_rating(place_id)
    cache.invalidate_prefix(f'nearby_{place_id}')
    cache.invalidate_prefix('places_')
    return jsonify({'success':True,'review':review}), 201
