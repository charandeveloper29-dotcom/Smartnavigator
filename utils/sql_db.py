"""SQLite Database Helper Functions"""
import sqlite3
import json
import math
from flask import g, current_app

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db(db_path):
    """Initialize database with schema"""
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password TEXT,
            avatar TEXT,
            avatar_url TEXT,
            bio TEXT,
            otp_verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add missing columns to existing users table if they don't exist
    existing_columns = [row[1] for row in db.execute('PRAGMA table_info(users)').fetchall()]
    for col, definition in [
        ('password',     'TEXT'),
        ('avatar',       'TEXT'),
        ('otp_verified', 'INTEGER DEFAULT 0'),
    ]:
        if col not in existing_columns:
            db.execute(f'ALTER TABLE users ADD COLUMN {col} {definition}')

    db.execute('''
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'India',
            category TEXT,
            description TEXT,
            latitude REAL,
            longitude REAL,
            rating REAL DEFAULT 4.5,
            images TEXT,
            entry_fee INTEGER DEFAULT 0,
            visit_duration TEXT,
            timings TEXT,
            best_time TEXT,
            featured INTEGER DEFAULT 0,
            user_added INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS saved_places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            place_id INTEGER NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (place_id) REFERENCES places (id),
            UNIQUE(user_id, place_id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            place_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (place_id) REFERENCES places (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS otp_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            purpose TEXT DEFAULT 'register',
            attempts INTEGER DEFAULT 0,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.commit()
    db.close()
    print('[DB] SQLite database initialized → database/smart_navigator.db')


# ==================== CRUD Operations ====================

def db_get_all(table):
    """Get all rows from a table"""
    db = get_db()
    rows = db.execute(f'SELECT * FROM {table}').fetchall()
    return [dict(row) for row in rows]

def db_get_by_id(table, id):
    """Get single row by ID"""
    db = get_db()
    row = db.execute(f'SELECT * FROM {table} WHERE id = ?', (id,)).fetchone()
    return dict(row) if row else None

def db_insert(table, data):
    """Insert a new row and return the full inserted row as a dict"""
    db = get_db()
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data])
    query = f'INSERT INTO {table} ({columns}) VALUES ({placeholders})'
    cursor = db.execute(query, list(data.values()))
    db.commit()
    row = db.execute(f'SELECT * FROM {table} WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return dict(row) if row else None

def db_update(table, id, data):
    """Update row by ID"""
    db = get_db()
    updates = ', '.join([f'{k} = ?' for k in data.keys()])
    values = list(data.values()) + [id]
    db.execute(f'UPDATE {table} SET {updates} WHERE id = ?', values)
    db.commit()

def db_find_by(table, column, value):
    """Find rows by column value"""
    db = get_db()
    rows = db.execute(f'SELECT * FROM {table} WHERE {column} = ?', (value,)).fetchall()
    return [dict(row) for row in rows]

def db_execute(query, params=()):
    """Execute a raw query"""
    db = get_db()
    cursor = db.execute(query, params)
    db.commit()
    return cursor


# ==================== User Functions ====================

def get_user_by_email(email):
    """Get user by email"""
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    return dict(row) if row else None

def get_user_by_phone(phone):
    """Get user by phone"""
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE phone = ?', (phone,)).fetchone()
    return dict(row) if row else None


# ==================== Places Functions ====================

def search_places(query):
    """Search places by name, city, state, description"""
    db = get_db()
    search_term = f'%{query}%'
    rows = db.execute('''
        SELECT * FROM places
        WHERE name LIKE ? OR city LIKE ? OR state LIKE ? OR description LIKE ?
        ORDER BY rating DESC
        LIMIT 20
    ''', (search_term, search_term, search_term, search_term)).fetchall()
    return [dict(row) for row in rows]

def get_places_paginated(page=1, per_page=9, category='all'):
    """Get paginated places"""
    db = get_db()
    offset = (page - 1) * per_page

    if category == 'all':
        rows = db.execute(
            'SELECT * FROM places ORDER BY rating DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()
        total = db.execute('SELECT COUNT(*) as count FROM places').fetchone()['count']
    else:
        rows = db.execute(
            'SELECT * FROM places WHERE category = ? ORDER BY rating DESC LIMIT ? OFFSET ?',
            (category, per_page, offset)
        ).fetchall()
        total = db.execute(
            'SELECT COUNT(*) as count FROM places WHERE category = ?',
            (category,)
        ).fetchone()['count']

    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return {
        'items':    [dict(row) for row in rows],
        'total':    total,
        'page':     page,
        'per_page': per_page,
        'pages':    total_pages,
        'has_prev': page > 1,
        'has_next': page < total_pages,
    }

def update_place_rating(place_id):
    """Recalculate and update place rating from reviews"""
    db = get_db()
    avg = db.execute(
        'SELECT AVG(rating) as avg_rating FROM reviews WHERE place_id = ?',
        (place_id,)
    ).fetchone()

    if avg and avg['avg_rating']:
        db.execute(
            'UPDATE places SET rating = ? WHERE id = ?',
            (round(avg['avg_rating'], 1), place_id)
        )
        db.commit()


# ==================== Saved Places Functions ====================

def get_user_saved_place_ids(user_id):
    """Get list of place IDs saved by user"""
    db = get_db()
    rows = db.execute('SELECT place_id FROM saved_places WHERE user_id = ?', (user_id,)).fetchall()
    return [row['place_id'] for row in rows]

def toggle_saved_place(user_id, place_id):
    """Toggle saved place for user"""
    db = get_db()
    existing = db.execute(
        'SELECT id FROM saved_places WHERE user_id = ? AND place_id = ?',
        (user_id, place_id)
    ).fetchone()

    if existing:
        db.execute('DELETE FROM saved_places WHERE user_id = ? AND place_id = ?', (user_id, place_id))
        db.commit()
        return 'unsaved'
    else:
        db.execute('INSERT INTO saved_places (user_id, place_id) VALUES (?, ?)', (user_id, place_id))
        db.commit()
        return 'saved'