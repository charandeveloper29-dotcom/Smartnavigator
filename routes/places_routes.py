"""Places Routes — now using SQLite via sql_db"""
from flask import Blueprint, request, jsonify, render_template
from utils.sql_db import (db_get_by_id, db_find_by, search_places,
                           get_places_paginated, db_get_all, update_place_rating)
from utils.auth_helper import get_current_user
from utils.geo_utils import get_nearby_places
from utils.cache import cache

places_bp = Blueprint('places', __name__)


@places_bp.route('/place/<int:place_id>')
def place_detail(place_id):
    place = db_get_by_id('places', place_id)
    if not place:
        return render_template('404.html'), 404
    hotels  = db_find_by('hotels',           'place_id', place_id)
    reviews = db_find_by('reviews',          'place_id', place_id)
    routes  = db_find_by('transport_routes', 'place_id', place_id)
    avg_rating = place.get('rating', 0) or 0
    if reviews:
        avg_rating = round(sum(r.get('rating',0) for r in reviews)/len(reviews), 1)
    user     = get_current_user()
    is_saved = False
    if user:
        from utils.sql_db import get_user_saved_place_ids
        is_saved = place_id in get_user_saved_place_ids(user['id'])
    return render_template('place.html', place=place, hotels=hotels,
                           reviews=reviews, routes=routes,
                           avg_rating=avg_rating, user=user, is_saved=is_saved)


@places_bp.route('/api/places')
def get_places():
    page     = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 9, type=int)
    category = request.args.get('category', '').lower()
    featured = request.args.get('featured', '').lower() == 'true'
    ck = f"places_{page}_{per_page}_{category}_{featured}"
    cached = cache.get(ck)
    if cached: return jsonify(cached)
    result = get_places_paginated(page, per_page, category=category)
    cache.set(ck, result, ttl=120)
    return jsonify(result)


@places_bp.route('/api/places/featured')
def get_featured():
    cached = cache.get('featured_places')
    if cached: return jsonify(cached)
    from utils.sql_db import db_paginate
    result = db_paginate('places', 1, 6, 'featured = 1', [], 'id')
    featured = result['items']
    cache.set('featured_places', featured, ttl=300)
    return jsonify(featured)


@places_bp.route('/api/places/search')
def search_places_api():
    query = request.args.get('q', '').strip()
    ck = f"search_{query.lower()}"
    cached = cache.get(ck)
    if cached: return jsonify(cached)
    results = search_places(query)
    slim = [{'id':p['id'],'name':p['name'],'city':p['city'],
             'state':p.get('state',''),'category':p['category'],
             'rating':p.get('rating',0),'images':p.get('images',[])}
            for p in results]
    cache.set(ck, slim, ttl=60)
    return jsonify(slim)


@places_bp.route('/api/places/<int:place_id>')
def get_place(place_id):
    place = db_get_by_id('places', place_id)
    if not place: return jsonify({'error':'Place not found'}), 404
    return jsonify(place)


@places_bp.route('/api/places/<int:place_id>/nearby')
def get_nearby(place_id):
    radius = request.args.get('radius', 20, type=float)
    limit  = request.args.get('limit',  8,  type=int)
    ck = f"nearby_{place_id}_{radius}_{limit}"
    cached = cache.get(ck)
    if cached: return jsonify(cached)
    current_place = db_get_by_id('places', place_id)
    if not current_place: return jsonify({'error':'Place not found'}), 404
    all_places = db_get_all('places')
    nearby = get_nearby_places(current_place, all_places, radius_km=radius, limit=limit)
    for p in nearby:
        dist = p.get('distance', 0)
        p['distance_formatted'] = f"{dist:.1f} km" if dist >= 1 else f"{int(dist*1000)} m"
    result = {
        'center': {'id':current_place['id'],'name':current_place['name'],
                   'latitude':current_place['latitude'],'longitude':current_place['longitude']},
        'radius_km': radius, 'count': len(nearby), 'places': nearby
    }
    cache.set(ck, result, ttl=300)
    return jsonify(result)


@places_bp.route('/api/places/<int:place_id>/hotels')
def get_place_hotels(place_id):
    hotels = db_find_by('hotels', 'place_id', place_id)
    hotels.sort(key=lambda h: h.get('rating',0), reverse=True)
    return jsonify(hotels)


@places_bp.route('/api/places/<int:place_id>/routes')
def get_place_routes(place_id):
    return jsonify(db_find_by('transport_routes', 'place_id', place_id))
