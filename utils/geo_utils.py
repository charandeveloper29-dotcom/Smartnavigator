"""
Geo Utilities Module
Haversine distance calculation and nearby places logic
"""

import math


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on Earth using the Haversine formula.
    
    Args:
        lat1, lon1: Latitude/longitude of point 1 (decimal degrees)
        lat2, lon2: Latitude/longitude of point 2 (decimal degrees)
    
    Returns:
        Distance in kilometers (float)
    """
    # Convert decimal degrees to radians
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    lon1_r = math.radians(lon1)
    lon2_r = math.radians(lon2)

    # Haversine formula
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    # Earth's radius in kilometers
    R = 6371
    return R * c


def get_nearby_places(current_place, all_places, radius_km=20, limit=10):
    """
    Find places within a given radius from a reference place.
    
    Args:
        current_place: dict with latitude and longitude
        all_places: list of all place dicts
        radius_km: search radius in kilometers
        limit: maximum number of results to return
    
    Returns:
        List of nearby places sorted by distance, with 'distance' field added
    """
    lat1 = current_place.get('latitude')
    lon1 = current_place.get('longitude')
    
    if lat1 is None or lon1 is None:
        return []

    nearby = []
    for place in all_places:
        # Skip the current place itself
        if place.get('id') == current_place.get('id'):
            continue

        lat2 = place.get('latitude')
        lon2 = place.get('longitude')

        if lat2 is None or lon2 is None:
            continue

        distance = haversine_distance(lat1, lon1, lat2, lon2)

        if distance <= radius_km:
            place_copy = dict(place)
            place_copy['distance'] = round(distance, 1)
            nearby.append(place_copy)

    # Sort by distance ascending
    nearby.sort(key=lambda x: x['distance'])
    return nearby[:limit]


def format_distance(km):
    """Format distance for display."""
    if km < 1:
        return f"{int(km * 1000)} m"
    return f"{km:.1f} km"
