"""
Smart Navigator - Services Routes
Handles external service integrations (Swiggy, PharmEasy, Rapido)
"""

from flask import Blueprint, jsonify, request

services_bp = Blueprint('services', __name__, url_prefix='/api/services')


# ─── Service Configuration ────────────────────────────────────────────────────
SERVICES = {
    'swiggy': {
        'name': 'Swiggy',
        'icon': '🍽️',
        'color': '#FC8019',
        'description': 'Order Food',
        'base_url': 'https://www.swiggy.com'
    },
    'pharmeasy': {
        'name': 'PharmEasy',
        'icon': '💊',
        'color': '#10847E',
        'description': 'Order Medicine',
        'base_url': 'https://pharmeasy.in'
    },
    'rapido': {
        'name': 'Rapido',
        'icon': '🏍️',
        'color': '#FFC700',
        'description': 'Book Ride',
        'base_url': 'https://www.rapido.bike'
    }
}


# ─── Get All Services ────────────────────────────────────────────────────────
@services_bp.route('/', methods=['GET'])
def get_services():
    """Get all available services"""
    return jsonify({
        'success': True,
        'services': SERVICES
    })


# ─── Get Service URL ─────────────────────────────────────────────────────────
@services_bp.route('/<service_id>/url', methods=['GET'])
def get_service_url(service_id):
    """Get redirect URL for a service"""
    if service_id not in SERVICES:
        return jsonify({
            'success': False,
            'error': 'Service not found'
        }), 404
    
    city = request.args.get('city', '')
    
    # Construct URL based on service
    service = SERVICES[service_id]
    url = service['base_url']
    
    # Add city parameter if available
    if city:
        if service_id == 'swiggy':
            url = f"{url}/city/{city.lower().replace(' ', '-')}"
        elif service_id == 'pharmeasy':
            url = f"{url}?city={city}"
        elif service_id == 'rapido':
            url = f"{url}?city={city}"
    
    return jsonify({
        'success': True,
        'url': url,
        'service': service
    })