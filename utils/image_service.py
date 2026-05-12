"""
Place Image Service
Fetches real images for ANY place using:
1. Wikipedia API (free, no key needed)
2. OpenStreetMap Nominatim for geocoding (free, no key needed)
3. Wikimedia Commons for photos (free, no key needed)
"""

import urllib.request
import urllib.parse
import json
import re


def get_wikipedia_image(place_name, city="", country="India"):
    """
    Fetch real image URL from Wikipedia for any place name.
    Uses Wikipedia's free API - no key needed.
    Returns image URL string or None.
    """
    # Try different search queries - most specific first
    queries = [
        f"{place_name} {city}",
        f"{place_name} {country}",
        place_name,
    ]

    for query in queries:
        try:
            # Step 1: Search Wikipedia for the article
            search_url = (
                "https://en.wikipedia.org/w/api.php?"
                "action=query&list=search&format=json"
                f"&srsearch={urllib.parse.quote(query)}&srlimit=3"
            )
            req = urllib.request.Request(search_url,
                headers={'User-Agent': 'SmartNavigator/1.0 (travel app)'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            pages = data.get("query", {}).get("search", [])
            if not pages:
                continue

            page_title = pages[0]["title"]

            # Step 2: Get the main image from that article
            img_url = (
                "https://en.wikipedia.org/w/api.php?"
                "action=query&prop=pageimages&format=json&pithumbsize=800"
                f"&titles={urllib.parse.quote(page_title)}"
            )
            req2 = urllib.request.Request(img_url,
                headers={'User-Agent': 'SmartNavigator/1.0 (travel app)'})
            with urllib.request.urlopen(req2, timeout=5) as resp2:
                data2 = json.loads(resp2.read().decode())

            pages2 = data2.get("query", {}).get("pages", {})
            for page in pages2.values():
                thumbnail = page.get("thumbnail", {})
                if thumbnail and thumbnail.get("source"):
                    return thumbnail["source"]

        except Exception:
            continue

    return None


def get_nominatim_place(place_name, city="", country="India"):
    """
    Geocode a place using OpenStreetMap Nominatim (free, no key).
    Returns dict with lat, lon, display_name.
    """
    query = f"{place_name} {city} {country}".strip()
    url = (
        "https://nominatim.openstreetmap.org/search?"
        f"q={urllib.parse.quote(query)}&format=json&limit=1&addressdetails=1"
    )
    try:
        req = urllib.request.Request(url,
            headers={'User-Agent': 'SmartNavigator/1.0 (travel app)'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            results = json.loads(resp.read().decode())
            if results:
                r = results[0]
                return {
                    "lat": float(r["lat"]),
                    "lon": float(r["lon"]),
                    "display_name": r.get("display_name", ""),
                    "type": r.get("type", ""),
                    "osm_id": r.get("osm_id", "")
                }
    except Exception:
        pass
    return None


def get_place_image_url(place_name, city="", state="", country="India"):
    """
    Master function: get the best real image URL for any place.
    Tries Wikipedia first, falls back to a category-based Unsplash image.
    """
    # Try Wikipedia
    img = get_wikipedia_image(place_name, city, country)
    if img:
        return img

    # Fallback: deterministic Unsplash URL based on place name
    # These are curated travel photos that look good
    FALLBACK_IMAGES = {
        "heritage": "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800&q=80",
        "nature":   "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=800&q=80",
        "beach":    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80",
        "hill":     "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&q=80",
        "city":     "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=80",
    }
    return FALLBACK_IMAGES.get("nature")  # generic fallback


if __name__ == "__main__":
    # Quick test
    test_places = [
        ("Eiffel Tower", "Paris", "France"),
        ("Colosseum", "Rome", "Italy"),
        ("Times Square", "New York", "USA"),
        ("Hampi", "Karnataka", "India"),
    ]
    for name, city, country in test_places:
        img = get_place_image_url(name, city, country=country)
        print(f"{name}: {img[:70] if img else 'None'}...")
