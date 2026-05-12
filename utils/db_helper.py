"""
Database Helper Module
Handles all TXT/JSON file read, write, update and delete operations
"""

import json
import os
import threading
from datetime import datetime

# Thread lock for safe concurrent file access
_file_locks = {}
_locks_lock = threading.Lock()

DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database')


def _get_lock(filename):
    """Get or create a threading lock for a specific file."""
    with _locks_lock:
        if filename not in _file_locks:
            _file_locks[filename] = threading.Lock()
        return _file_locks[filename]


def _get_filepath(filename):
    """Get absolute path for a database file."""
    return os.path.join(DATABASE_DIR, filename)


def read_file(filename):
    """
    Read all records from a JSON/TXT database file.
    Returns a list of dictionaries, or empty list on error.
    """
    filepath = _get_filepath(filename)
    lock = _get_lock(filename)

    with lock:
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[DB ERROR] Reading {filename}: {e}")
            return []


def write_file(filename, data):
    """
    Write entire data list to a JSON/TXT database file.
    Overwrites existing content.
    """
    filepath = _get_filepath(filename)
    lock = _get_lock(filename)

    with lock:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except (IOError, TypeError) as e:
            print(f"[DB ERROR] Writing {filename}: {e}")
            return False


def get_next_id(filename):
    """Get the next available auto-increment ID for a file."""
    records = read_file(filename)
    if not records:
        return 1
    return max(record.get('id', 0) for record in records) + 1


def find_by_id(filename, record_id):
    """Find a single record by its ID."""
    records = read_file(filename)
    for record in records:
        if record.get('id') == record_id:
            return record
    return None


def find_by_field(filename, field, value):
    """Find all records where field matches value."""
    records = read_file(filename)
    return [r for r in records if r.get(field) == value]


def find_one_by_field(filename, field, value):
    """Find first record where field matches value."""
    records = read_file(filename)
    for record in records:
        if record.get(field) == value:
            return record
    return None


def insert_record(filename, record):
    """
    Insert a new record into a file.
    Auto-assigns ID and created_at timestamp.
    Returns the inserted record with assigned ID.
    """
    records = read_file(filename)
    record['id'] = get_next_id(filename)
    if 'created_at' not in record:
        record['created_at'] = datetime.now().isoformat()
    records.append(record)
    if write_file(filename, records):
        return record
    return None


def update_record(filename, record_id, updates):
    """
    Update a record by ID with provided fields.
    Returns updated record or None if not found.
    """
    records = read_file(filename)
    for i, record in enumerate(records):
        if record.get('id') == record_id:
            records[i].update(updates)
            records[i]['updated_at'] = datetime.now().isoformat()
            if write_file(filename, records):
                return records[i]
            return None
    return None


def delete_record(filename, record_id):
    """
    Delete a record by ID.
    Returns True if deleted, False if not found.
    """
    records = read_file(filename)
    original_count = len(records)
    records = [r for r in records if r.get('id') != record_id]
    if len(records) < original_count:
        return write_file(filename, records)
    return False


def search_records(filename, query, fields):
    """
    Search records across specified fields (case-insensitive).
    Returns list of matching records.
    """
    records = read_file(filename)
    query_lower = query.lower()
    results = []
    for record in records:
        for field in fields:
            value = record.get(field, '')
            if isinstance(value, list):
                value = ' '.join(str(v) for v in value)
            if query_lower in str(value).lower():
                if record not in results:
                    results.append(record)
                break
    return results


def paginate(records, page, per_page):
    """
    Paginate a list of records.
    Returns dict with items, total, pages, current_page.
    """
    total = len(records)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return {
        'items': records[start:end],
        'total': total,
        'pages': total_pages,
        'current_page': page,
        'per_page': per_page,
        'has_prev': page > 1,
        'has_next': page < total_pages
    }
