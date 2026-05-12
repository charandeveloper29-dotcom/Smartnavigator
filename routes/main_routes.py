from flask import Blueprint, render_template, request, session, redirect, url_for
from utils.sql_db import db_get_all, search_places, get_places_paginated
import json

# 1. Define the Blueprint BEFORE any other custom logic
main_bp = Blueprint('main', __name__)

# 2. Define your routes
@main_bp.route('/')
def index():
    """Home page showing featured places"""
    try:
        # Fetching top 6 featured places from the database
        all_places = db_get_all('places')
        # Filter for featured=1 if you have that column, otherwise just take first 6
        featured_places = [p for p in all_places if p.get('featured') == 1]
        if not featured_places:
            featured_places = all_places[:6]
    except Exception as e:
        print(f"[ERROR] Could not fetch featured places: {e}")
        featured_places = []
        
    return render_template('splash.html', places=featured_places)


@main_bp.route('/home')
def home():
    """Home page after login"""
    try:
        all_places = db_get_all('places')
        featured_places = [p for p in all_places if p.get('featured') == 1]
        if not featured_places:
            featured_places = all_places[:6]
    except Exception as e:
        print(f"[ERROR] Could not fetch places: {e}")
        featured_places = []
        
    return render_template('home.html', places=featured_places)


@main_bp.route('/explore')
def explore():
    """Exploration page with search and category filtering"""
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    page = request.args.get('page', 1, type=int)
    
    if query:
        # Search functionality
        results = search_places(query)
        pagination = {
            'items': results,
            'total': len(results),
            'pages': 1,
            'page': 1,
            'has_prev': False,
            'has_next': False
        }
    else:
        # Paginated browsing
        pagination = get_places_paginated(page=page, per_page=9, category=category)
        
    return render_template('explore.html', 
                           pagination=pagination, 
                           query=query, 
                           category=category)


@main_bp.route('/search')
def search_page():
    """Search results page"""
    query = request.args.get('q', '').strip()
    
    if not query:
        # No search query, redirect to explore
        return redirect(url_for('main.explore'))
    
    # Search places
    results = search_places(query)
    
    # Create pagination-like structure for template compatibility
    pagination = {
        'items': results,
        'total': len(results),
        'pages': 1,
        'page': 1,
        'has_prev': False,
        'has_next': False
    }
    
    return render_template('explore.html', 
                           pagination=pagination, 
                           query=query, 
                           category='all')


@main_bp.route('/map')
def map_page():
    """Interactive map page"""
    try:
        all_places = db_get_all('places')
        # Convert to JSON string for JavaScript
        places_json = json.dumps(all_places)
    except Exception as e:
        print(f"[ERROR] Could not fetch places for map: {e}")
        all_places = []
        places_json = '[]'
    
    return render_template('map.html', places_json=places_json)


@main_bp.route('/about')
def about():
    """About us page"""
    return render_template('about.html')


@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')


@main_bp.route('/set_location', methods=['POST'])
def set_location():
    """Update user location in session"""
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    if lat and lon:
        session['user_location'] = {'lat': float(lat), 'lon': float(lon)}
    return {"status": "success"}, 200