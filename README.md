# 🧭 Smart Navigator

**A production-ready travel exploration web app built with Python Flask + TXT file database.**

Discover India's finest destinations — heritage sites, beaches, hill stations, nature escapes, and cities — with nearby places, hotels, transport routes, and traveller reviews.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 Splash Page | Animated landing with language selector |
| 🔐 Authentication | JWT + session-based login/register |
| 🔍 Smart Search | Autocomplete search with debouncing |
| 🗂️ Categories | Heritage, Nature, Beach, Hill, City |
| 📍 Place Detail | Full info: timings, fees, ratings |
| 🗺️ Nearby Places | Haversine-based radius search |
| 🏨 Hotels | Filtered by place, with amenities |
| 🚆 Routes | Train, bus, flight, cab info |
| 🧮 Cost Estimator | JS-based trip budget calculator |
| ⭐ Reviews | Add & view per-place reviews |
| ❤️ Save Places | Bookmark favourites to profile |
| 📄 Pagination | Paginated place listing |
| ⚡ Caching | In-memory TTL cache |

---

## 🗂 Project Structure

```
smart_navigator/
├── app.py                    # Flask application factory
├── requirements.txt
├── .env.example
│
├── database/                 # TXT/JSON flat-file database
│   ├── users.txt
│   ├── places.txt
│   ├── hotels.txt
│   ├── reviews.txt
│   ├── saved_places.txt
│   └── transport_routes.txt
│
├── routes/                   # Flask Blueprints
│   ├── main_routes.py        # Splash, home, explore, search
│   ├── auth_routes.py        # Login, register, logout
│   ├── places_routes.py      # Places API + nearby
│   ├── reviews_routes.py     # Reviews CRUD
│   └── profile_routes.py     # Profile + saved places
│
├── utils/
│   ├── db_helper.py          # File read/write/search/paginate
│   ├── auth_helper.py        # JWT, password hashing, decorators
│   ├── geo_utils.py          # Haversine formula
│   └── cache.py              # In-memory TTL cache
│
├── templates/
│   ├── base.html             # Navbar + footer layout
│   ├── splash.html           # Landing page
│   ├── home.html             # Home with search + featured
│   ├── explore.html          # Paginated place grid
│   ├── place.html            # Place detail (full)
│   ├── login.html            # Login + Register
│   ├── profile.html          # User profile + saved
│   ├── search.html           # Search results
│   ├── 404.html
│   └── 500.html
│
└── static/
    ├── css/
    │   ├── main.css          # Global styles
    │   ├── splash.css        # Splash page styles
    │   └── auth.css          # Auth page styles
    ├── js/
    │   ├── main.js           # Global JS (save, reviews, tabs)
    │   ├── home.js           # Autocomplete + cost calculator
    │   ├── place.js          # Nearby places loader
    │   ├── explore.js        # Paginated grid + category filter
    │   ├── auth.js           # Login/register forms
    │   ├── profile.js        # Profile editing + logout
    │   └── splash.js         # Ribbon + language selector
    └── images/
        ├── favicon.svg
        ├── places/           # Place images (upload here)
        └── hotels/           # Hotel images (upload here)
```

---

## 🚀 Quick Start

### 1. Clone / Extract the project

```bash
cd smart_navigator
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional)

```bash
cp .env.example .env
# Edit .env and set a strong SECRET_KEY
```

### 5. Run the app

```bash
python app.py
```

Open your browser at **http://127.0.0.1:5000**

---

## 🗄️ Database (TXT Files)

All data is stored as JSON arrays in plain text files under `database/`.

### File Format

```json
[
  {
    "id": 1,
    "name": "Taj Mahal",
    "latitude": 27.1751,
    "longitude": 78.0421,
    ...
  }
]
```

### Helper Functions (`utils/db_helper.py`)

| Function | Description |
|---|---|
| `read_file(filename)` | Read all records |
| `write_file(filename, data)` | Overwrite file |
| `find_by_id(filename, id)` | Find by ID |
| `find_by_field(filename, field, value)` | Filter by field |
| `insert_record(filename, record)` | Insert + auto-ID |
| `update_record(filename, id, updates)` | Partial update |
| `delete_record(filename, id)` | Remove by ID |
| `search_records(filename, query, fields)` | Full-text search |
| `paginate(records, page, per_page)` | Slice + metadata |

---

## 📡 API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET  | `/api/auth/me` | Current user info |

### Places
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/places` | Paginated list (`?page=1&category=beach`) |
| GET | `/api/places/featured` | Featured places |
| GET | `/api/places/search` | Search (`?q=manali`) |
| GET | `/api/places/<id>` | Single place |
| GET | `/api/places/<id>/nearby` | Nearby places (`?radius=20`) |
| GET | `/api/places/<id>/hotels` | Hotels for place |
| GET | `/api/places/<id>/routes` | Transport routes |

### Reviews
| Method | Endpoint | Description |
|---|---|---|
| GET  | `/api/places/<id>/reviews` | Get reviews |
| POST | `/api/places/<id>/reviews` | Add review (auth required) |

### Profile
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/profile` | Get profile |
| PUT | `/api/profile` | Update name |
| POST | `/api/places/<id>/save` | Toggle save |
| GET | `/api/profile/saved-places` | Saved places list |

---

## 🗺️ Nearby Places Algorithm

Uses the **Haversine Formula** to compute great-circle distances between coordinates:

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    lat1_r = math.radians(lat1)
    lat2_r = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2)
    c = 2 * math.asin(math.sqrt(a))
    return 6371 * c  # km
```

Called via: `GET /api/places/<id>/nearby?radius=50&limit=8`

---

## 🔐 Authentication Flow

1. User submits email + password
2. Server hashes password with **PBKDF2-HMAC-SHA256** (260,000 iterations)
3. On login, server creates a **custom JWT token** (HS256 signed)
4. Token stored in **HTTP-only cookie** + Flask session
5. Protected routes use `@login_required` decorator

---

## 🎨 Design System

- **Fonts**: Playfair Display (headings) + DM Sans (body)
- **Primary**: `#C9A84C` (warm gold)
- **Background**: `#F5F2EE` (warm fog)
- **Dark**: `#1A1614` (deep ink)
- **Aesthetic**: Warm editorial travel magazine

---

## 📦 Dependencies

```
Flask==3.0.3
Werkzeug==3.0.3
python-dotenv==1.0.1
```

No database drivers, no ORMs, no heavy frameworks — just pure Python + flat files.

---

## 🧪 Demo Credentials

After running the app, register any new account via `/register`, or use the existing sample data users:

- **Email**: `arjun@example.com`
- **Password**: Create a new account (sample passwords are hashed placeholders)

---

## 🛠️ Extending the App

### Add a new place
Edit `database/places.txt` and add a JSON object with all required fields.

### Add a new hotel
Edit `database/hotels.txt` — set `place_id` to match the place's `id`.

### Add transport routes
Edit `database/transport_routes.txt` — set `place_id` to match.

### Change cache TTL
In `utils/cache.py`, adjust the `ttl` parameter in `cache.set()` calls.

---

## 🚧 Known Limitations

- Image display uses CSS gradient backgrounds (add real `.jpg` files to `static/images/places/` and update `places.txt` `images` field)
- No email verification
- No password reset flow
- Single-server only (file locks are process-scoped)

---

Built with ❤️ for Indian travellers · Smart Navigator © 2024
