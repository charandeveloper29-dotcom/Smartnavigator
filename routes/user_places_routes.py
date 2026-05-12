"""User Places Routes — SQLite"""
from flask import Blueprint, request, jsonify, render_template
from utils.sql_db import db_get_all, db_insert, db_get_by_id
from utils.auth_helper import get_current_user
from utils.cache import cache
import urllib.request, urllib.parse, json

user_places_bp = Blueprint('user_places', __name__)


@user_places_bp.route('/add-place')
def add_place_page():
    """Show add place form"""
    return render_template('add_place.html')


def fetch_wiki_image(place_name, hint=""):
    for query in [f"{place_name} {hint}".strip(), place_name]:
        try:
            url = (f"https://en.wikipedia.org/w/api.php?"
                   f"action=query&list=search&format=json&srlimit=3"
                   f"&srsearch={urllib.parse.quote(query)}")
            req = urllib.request.Request(url, headers={'User-Agent':'SmartNavigator/1.0'})
            with urllib.request.urlopen(req, timeout=6) as r:
                data = json.loads(r.read().decode())
            results = data.get("query",{}).get("search",[])
            if not results: continue
            title = results[0]["title"]
            url2 = (f"https://en.wikipedia.org/w/api.php?"
                    f"action=query&prop=pageimages&format=json&pithumbsize=900"
                    f"&titles={urllib.parse.quote(title)}")
            req2 = urllib.request.Request(url2, headers={'User-Agent':'SmartNavigator/1.0'})
            with urllib.request.urlopen(req2, timeout=6) as r2:
                data2 = json.loads(r2.read().decode())
            for page in data2.get("query",{}).get("pages",{}).values():
                src = page.get("thumbnail",{}).get("source")
                if src: return src
        except Exception: continue
    return None


def fetch_nominatim(name, hint=""):
    url = (f"https://nominatim.openstreetmap.org/search?"
           f"q={urllib.parse.quote(f'{name} {hint}'.strip())}&format=json&limit=1&addressdetails=1")
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'SmartNavigator/1.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            results = json.loads(r.read().decode())
        if results:
            res  = results[0]
            addr = res.get("address",{})
            return {
                "lat":     float(res["lat"]), "lon": float(res["lon"]),
                "city":    addr.get("city") or addr.get("town") or addr.get("village",""),
                "state":   addr.get("state",""),
                "country": addr.get("country","")
            }
    except Exception: pass
    return None


def guess_category(name, display=""):
    text = (name+" "+display).lower()
    if any(w in text for w in ["beach","coast","sea","shore","island","bay"]): return "beach"
    if any(w in text for w in ["mountain","hill","peak","valley","forest","lake","river","waterfall","national park","wildlife","nature","garden"]): return "nature"
    if any(w in text for w in ["fort","palace","temple","mosque","church","monument","heritage","ruins","ancient","museum","tomb","gate","mahal","mandir"]): return "heritage"
    if any(w in text for w in ["hill station","snow","trek","altitude","himalayas","station"]): return "hill"
    if any(w in text for w in ["city","town","market","street","square","downtown","metro"]): return "city"
    return "heritage"


FALLBACKS = {
    "heritage":"https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=800",
    "nature":  "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=800",
    "beach":   "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800",
    "hill":    "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800",
    "city":    "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800",
}


@user_places_bp.route('/api/search-any-place')
def search_any_place():
    q = request.args.get('q','').strip()
    if len(q) < 2: return jsonify([])
    ck = f"place_search_{q.lower()}"
    cached = cache.get(ck)
    if cached: return jsonify(cached)
    url = (f"https://nominatim.openstreetmap.org/search?"
           f"q={urllib.parse.quote(q)}&format=json&limit=8&addressdetails=1")
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'SmartNavigator/1.0'})
        with urllib.request.urlopen(req, timeout=6) as r:
            results = json.loads(r.read().decode())
        suggestions = []
        for res in results:
            addr = res.get("address",{})
            city  = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("county","")
            state = addr.get("state","")
            country = addr.get("country","")
            parts = [p for p in [city, state, country] if p]
            suggestions.append({
                "osm_id":  res.get("osm_id"),
                "name":    res.get("display_name","").split(",")[0].strip(),
                "full_name":res.get("display_name",""),
                "short":   ", ".join(parts[:3]),
                "lat":     float(res["lat"]), "lon": float(res["lon"]),
                "type":    res.get("type",""),
                "city":    city, "state": state, "country": country,
            })
        cache.set(ck, suggestions, ttl=300)
        return jsonify(suggestions)
    except Exception:
        return jsonify([])


@user_places_bp.route('/api/places/add', methods=['POST'])
def add_place():
    data = request.get_json()
    if not data: return jsonify({'error':'No data provided'}), 400
    name    = data.get('name','').strip()
    city    = data.get('city','').strip()
    state   = data.get('state','').strip()
    country = data.get('country','India').strip()
    lat     = data.get('latitude')
    lon     = data.get('longitude')
    desc    = data.get('description','').strip()
    cat     = data.get('category','').strip()
    if not name: return jsonify({'error':'Place name is required'}), 400

    if not lat or not lon:
        geo = fetch_nominatim(name, f"{city} {country}")
        if geo:
            lat = geo['lat']; lon = geo['lon']
            if not city:  city  = geo['city']
            if not state: state = geo['state']
            if not country or country == 'India': country = geo['country'] or country

    if not cat: cat = guess_category(name, f"{city} {state}")

    hint      = f"{city} {state} {country}".strip()
    image_url = fetch_wiki_image(name, hint) or FALLBACKS.get(cat, FALLBACKS["heritage"])

    if not desc:
        parts = [name]
        if city:    parts.append(f"in {city}")
        if state:   parts.append(f", {state}")
        if country: parts.append(f", {country}")
        desc = "".join(parts) + ". A remarkable destination worth visiting."

    # ✅ Insert place and get the ID
    place_id = db_insert('places', {
        'name': name, 
        'city': city or name, 
        'state': state or country,
        'country': country, 
        'category': cat, 
        'description': desc,
        'latitude': lat or 0.0, 
        'longitude': lon or 0.0,
        'entry_fee': data.get('entry_fee', 0),
        'timings': data.get('timings', 'Open all day'),
        'best_time': data.get('best_time', 'Year round'),
        'rating': 4.5,
        'images': image_url,  # Store as string
        'featured': 0,
        'visit_duration': data.get('visit_duration', '2-4 hours'),
        'user_added': 1
    })
    
    # ✅ FIX: Get the full place object to return
    place_data = db_get_by_id('places', place_id)
    
    cache.invalidate_prefix('places_')
    cache.invalidate_prefix('search_')
    
    # ✅ Return the full place object (not just place_id)
    return jsonify({
        'success': True,
        'place': place_data,
        'image_fetched': image_url
    }), 201


@user_places_bp.route('/api/preview-place-image')
def preview_place_image():
    name    = request.args.get('name','').strip()
    city    = request.args.get('city','').strip()
    country = request.args.get('country','India').strip()
    if not name or len(name) < 3: return jsonify({'image':None})
    ck = f"preview_{name}_{city}_{country}".lower()
    cached = cache.get(ck)
    if cached is not None: return jsonify({'image':cached})
    image = fetch_wiki_image(name, f"{city} {country}".strip())
    cache.set(ck, image, ttl=600)
    return jsonify({'image':image})