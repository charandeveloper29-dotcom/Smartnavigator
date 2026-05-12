"""
Smart Navigator — Data Migration Script
Migrates all existing TXT/JSON database files into SQLite.
Run once: python migrate.py
"""

import os
import sys
import json

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sql_db import init_db, db_insert, get_connection, get_cursor, _prep_json
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(__file__), 'database')


def load_txt(filename):
    path = os.path.join(DB_DIR, filename)
    if not os.path.exists(path):
        print(f"  [skip] {filename} not found")
        return []
    with open(path, encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"  [error] {filename}: {e}")
            return []


def migrate():
    print("=" * 55)
    print("  Smart Navigator — Migrating to SQLite")
    print("=" * 55)

    # Initialise schema
    init_db()

    conn = get_connection()
    cur  = conn.cursor()

    # ── 1. USERS ──────────────────────────────────────────
    print("\n[1/6] Migrating users…")
    users = load_txt('users.txt')
    cur.execute("DELETE FROM users")
    for u in users:
        saved_ids = u.pop('saved_places', [])   # stored separately
        row = {
            'id':           u.get('id'),
            'name':         u.get('name', ''),
            'email':        u.get('email', ''),
            'phone':        u.get('phone', ''),
            'password':     u.get('password', ''),
            'avatar':       u.get('avatar', ''),
            'avatar_url':   u.get('avatar_url', ''),
            'bio':          u.get('bio', ''),
            'otp_verified': int(u.get('otp_verified', False)),
            'created_at':   u.get('created_at', datetime.now().isoformat()),
        }
        cur.execute("""
            INSERT OR REPLACE INTO users
            (id,name,email,phone,password,avatar,avatar_url,bio,otp_verified,created_at)
            VALUES (:id,:name,:email,:phone,:password,:avatar,:avatar_url,:bio,:otp_verified,:created_at)
        """, row)
        # Re-attach saved_places to the user object for later
        u['_saved_ids'] = saved_ids
    conn.commit()
    print(f"  ✅ {len(users)} users migrated")

    # ── 2. PLACES ─────────────────────────────────────────
    print("\n[2/6] Migrating places…")
    places = load_txt('places.txt')
    cur.execute("DELETE FROM places")
    for p in places:
        row = {
            'id':                p.get('id'),
            'name':              p.get('name',''),
            'city':              p.get('city',''),
            'state':             p.get('state',''),
            'country':           p.get('country','India'),
            'category':          p.get('category','heritage'),
            'description':       p.get('description',''),
            'latitude':          float(p.get('latitude',0)),
            'longitude':         float(p.get('longitude',0)),
            'entry_fee':         int(p.get('entry_fee',0)),
            'entry_fee_foreign': int(p.get('entry_fee_foreign',0)),
            'timings':           p.get('timings','Open all day'),
            'best_time':         p.get('best_time','Year round'),
            'rating':            float(p.get('rating',0)),
            'review_count':      int(p.get('review_count',0)),
            'images':            json.dumps(p.get('images',[])),
            'tags':              json.dumps(p.get('tags',[])),
            'featured':          int(p.get('featured',False)),
            'visit_duration':    p.get('visit_duration','2-4 hours'),
            'user_added':        int(p.get('user_added',False)),
            'created_at':        p.get('created_at', datetime.now().isoformat()),
        }
        cur.execute("""
            INSERT OR REPLACE INTO places
            (id,name,city,state,country,category,description,latitude,longitude,
             entry_fee,entry_fee_foreign,timings,best_time,rating,review_count,
             images,tags,featured,visit_duration,user_added,created_at)
            VALUES (:id,:name,:city,:state,:country,:category,:description,:latitude,:longitude,
                    :entry_fee,:entry_fee_foreign,:timings,:best_time,:rating,:review_count,
                    :images,:tags,:featured,:visit_duration,:user_added,:created_at)
        """, row)
    conn.commit()
    print(f"  ✅ {len(places)} places migrated")

    # ── 3. HOTELS ─────────────────────────────────────────
    print("\n[3/6] Migrating hotels…")
    hotels = load_txt('hotels.txt')
    cur.execute("DELETE FROM hotels")
    for h in hotels:
        row = {
            'id':                  h.get('id'),
            'name':                h.get('name',''),
            'place_id':            h.get('place_id'),
            'city':                h.get('city',''),
            'category':            h.get('category','mid-range'),
            'description':         h.get('description',''),
            'price_per_night':     int(h.get('price_per_night',0)),
            'rating':              float(h.get('rating',0)),
            'review_count':        int(h.get('review_count',0)),
            'amenities':           json.dumps(h.get('amenities',[])),
            'contact':             h.get('contact',''),
            'email':               h.get('email',''),
            'address':             h.get('address',''),
            'images':              json.dumps(h.get('images',[])),
            'distance_from_place': float(h.get('distance_from_place',0)),
        }
        cur.execute("""
            INSERT OR REPLACE INTO hotels
            (id,name,place_id,city,category,description,price_per_night,rating,
             review_count,amenities,contact,email,address,images,distance_from_place)
            VALUES (:id,:name,:place_id,:city,:category,:description,:price_per_night,:rating,
                    :review_count,:amenities,:contact,:email,:address,:images,:distance_from_place)
        """, row)
    conn.commit()
    print(f"  ✅ {len(hotels)} hotels migrated")

    # ── 4. REVIEWS ────────────────────────────────────────
    print("\n[4/6] Migrating reviews…")
    reviews = load_txt('reviews.txt')
    cur.execute("DELETE FROM reviews")
    for r in reviews:
        row = {
            'id':            r.get('id'),
            'place_id':      r.get('place_id'),
            'user_id':       r.get('user_id'),
            'user_name':     r.get('user_name',''),
            'rating':        int(r.get('rating',5)),
            'title':         r.get('title',''),
            'content':       r.get('content',''),
            'helpful_count': int(r.get('helpful_count',0)),
            'created_at':    r.get('created_at', datetime.now().isoformat()),
        }
        cur.execute("""
            INSERT OR REPLACE INTO reviews
            (id,place_id,user_id,user_name,rating,title,content,helpful_count,created_at)
            VALUES (:id,:place_id,:user_id,:user_name,:rating,:title,:content,:helpful_count,:created_at)
        """, row)
    conn.commit()
    print(f"  ✅ {len(reviews)} reviews migrated")

    # ── 5. SAVED PLACES ───────────────────────────────────
    print("\n[5/6] Migrating saved places…")
    saved_records = load_txt('saved_places.txt')
    cur.execute("DELETE FROM saved_places")

    # Also migrate from user.saved_places arrays
    seen = set()
    for u in users:
        for pid in u.get('_saved_ids', []):
            key = (u['id'], pid)
            if key not in seen:
                seen.add(key)
                cur.execute("""
                    INSERT OR IGNORE INTO saved_places (user_id, place_id, saved_at)
                    VALUES (?, ?, ?)
                """, (u['id'], pid, datetime.now().isoformat()))

    for s in saved_records:
        key = (s.get('user_id'), s.get('place_id'))
        if key not in seen and key[0] and key[1]:
            seen.add(key)
            cur.execute("""
                INSERT OR IGNORE INTO saved_places (id, user_id, place_id, saved_at)
                VALUES (?,?,?,?)
            """, (s.get('id'), s['user_id'], s['place_id'],
                  s.get('saved_at', datetime.now().isoformat())))
    conn.commit()
    print(f"  ✅ {len(seen)} saved place records migrated")

    # ── 6. TRANSPORT ROUTES ───────────────────────────────
    print("\n[6/6] Migrating transport routes…")
    routes = load_txt('transport_routes.txt')
    cur.execute("DELETE FROM transport_routes")
    for rt in routes:
        row = {
            'id':              rt.get('id'),
            'from_city':       rt.get('from_city',''),
            'to_city':         rt.get('to_city',''),
            'place_id':        rt.get('place_id'),
            'mode':            rt.get('mode','train'),
            'operator':        rt.get('operator',''),
            'duration':        rt.get('duration',''),
            'distance':        int(rt.get('distance',0)),
            'cost_min':        int(rt.get('cost_min',0)),
            'cost_max':        int(rt.get('cost_max',0)),
            'frequency':       rt.get('frequency',''),
            'departure_times': json.dumps(rt.get('departure_times',[])),
            'booking_note':    rt.get('booking_note',''),
        }
        cur.execute("""
            INSERT OR REPLACE INTO transport_routes
            (id,from_city,to_city,place_id,mode,operator,duration,distance,
             cost_min,cost_max,frequency,departure_times,booking_note)
            VALUES (:id,:from_city,:to_city,:place_id,:mode,:operator,:duration,:distance,
                    :cost_min,:cost_max,:frequency,:departure_times,:booking_note)
        """, row)
    conn.commit()
    print(f"  ✅ {len(routes)} transport routes migrated")

    # ── VERIFY ────────────────────────────────────────────
    print("\n── Database Verification ──")
    for table in ['users','places','hotels','reviews','saved_places','transport_routes']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {table:25s} → {count} rows")

    print("\n✅ Migration complete!")
    print(f"   SQLite DB: {os.path.join(DB_DIR, 'smart_navigator.db')}")
    print("   TXT files kept as backup in database/ folder")


if __name__ == '__main__':
    migrate()
