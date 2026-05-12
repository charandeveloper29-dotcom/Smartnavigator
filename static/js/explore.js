/* ═══════════════════════════════════════════════════════
   Smart Navigator — explore.js
   Shows stored places + live search from OpenStreetMap
   + Wikipedia descriptions and images for any India place
═══════════════════════════════════════════════════════ */

let currentPage   = 1;
let currentCat    = 'all';
let currentSearch = '';
let searchTimer;
const PER_PAGE    = 9;

document.addEventListener('DOMContentLoaded', () => {
  currentCat = (INITIAL_CATEGORY || 'all').toLowerCase();

  // Mark active category tab
  document.querySelectorAll('.cat-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.cat === currentCat);
    tab.addEventListener('click', () => {
      document.querySelectorAll('.cat-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentCat    = tab.dataset.cat;
      currentPage   = 1;
      currentSearch = '';
      const searchEl = document.getElementById('exploreSearch');
      if (searchEl) searchEl.value = '';
      loadPlaces();
    });
  });

  // Search input
  const searchEl = document.getElementById('exploreSearch');
  if (searchEl) {
    searchEl.addEventListener('input', () => {
      clearTimeout(searchTimer);
      const q = searchEl.value.trim();
      currentSearch = q;
      currentPage   = 1;
      if (!q) {
        loadPlaces();
        return;
      }
      // Debounce 400ms then search
      searchTimer = setTimeout(() => searchAllPlaces(q), 400);
    });

    searchEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        clearTimeout(searchTimer);
        const q = searchEl.value.trim();
        if (q) searchAllPlaces(q);
      }
    });
  }

  loadPlaces();
});


// ── Load stored places (normal / category view) ──────
async function loadPlaces() {
  const grid    = document.getElementById('exploreGrid');
  const countEl = document.getElementById('placeCount');
  if (!grid) return;

  showSkeletons(grid);

  try {
    let url;
    if (currentSearch) {
      url = `/api/places/search?q=${encodeURIComponent(currentSearch)}`;
    } else {
      url = `/api/places?page=${currentPage}&per_page=${PER_PAGE}&category=${currentCat}`;
    }

    const res  = await fetch(url);
    const data = await res.json();

    // /api/places returns { items, total, pages, ... }
    // /api/places/search returns a plain array
    const items = Array.isArray(data) ? data : (data.items || []);
    const total = Array.isArray(data) ? data.length : (data.total || 0);

    if (countEl) countEl.textContent = `${total} place${total !== 1 ? 's' : ''} found`;

    if (items.length) {
      grid.innerHTML = items.map((p, i) => buildPlaceCard(p, i, false)).join('');
    } else {
      grid.innerHTML = emptyState('No places found');
    }

    if (!Array.isArray(data)) {
      renderPagination(data);
    } else {
      document.getElementById('pagination').innerHTML = '';
    }
  } catch (e) {
    grid.innerHTML = errorState();
  }
}


// ── Search: stored places + live OpenStreetMap ───────
async function searchAllPlaces(query) {
  const grid    = document.getElementById('exploreGrid');
  const countEl = document.getElementById('placeCount');
  const pagEl   = document.getElementById('pagination');
  if (!grid) return;

  showSkeletons(grid);
  if (countEl) countEl.textContent = 'Searching across India…';
  if (pagEl)   pagEl.innerHTML = '';

  try {
    // 1) Search our stored places
    const localRes   = await fetch(`/api/places/search?q=${encodeURIComponent(query)}`);
    const localPlaces = await localRes.json();

    // 2) Search OpenStreetMap for any India place (runs in parallel)
    const livePromise = fetchLivePlaces(query);

    // Show stored results immediately
    let cards = localPlaces.map((p, i) => buildPlaceCard(p, i, false));

    if (countEl) countEl.textContent = `${localPlaces.length} saved place${localPlaces.length !== 1 ? 's' : ''} found — searching more…`;
    grid.innerHTML = cards.join('') || '<div id="liveLoadingRow" style="grid-column:1/-1;text-align:center;padding:40px;color:#999"><span style="font-size:1.8rem">🔍</span><br>Searching all India places…</div>';

    // 3) Wait for live results
    const livePlaces = await livePromise;

    // Remove places already in stored results (by name match)
    const storedNames = new Set(localPlaces.map(p => p.name.toLowerCase()));
    const newLive = livePlaces.filter(p => !storedNames.has(p.name.toLowerCase()));

    const total = localPlaces.length + newLive.length;
    if (countEl) countEl.textContent = `${total} place${total !== 1 ? 's' : ''} found for "${query}"`;

    // Build all cards
    const allCards = [
      ...localPlaces.map((p, i) => buildPlaceCard(p, i, false)),
      ...newLive.map((p, i) => buildLiveCard(p, localPlaces.length + i))
    ];

    if (allCards.length) {
      grid.innerHTML = allCards.join('');
    } else {
      grid.innerHTML = emptyState(`No places found for "${query}".<br>Try a different spelling or search term.`);
    }

  } catch (e) {
    console.error(e);
    grid.innerHTML = errorState();
  }
}


// ── Fetch live places from OpenStreetMap Nominatim ──
async function fetchLivePlaces(query) {
  try {
    const url  = `https://nominatim.openstreetmap.org/search?` +
                 `q=${encodeURIComponent(query + ' India')}&format=json&limit=12` +
                 `&addressdetails=1&countrycodes=in&dedupe=1`;
    const res  = await fetch(url, {
      headers: { 'User-Agent': 'SmartNavigator/1.0' }
    });
    const data = await res.json();

    return data.map(r => {
      const addr  = r.address || {};
      const city  = addr.city || addr.town || addr.village || addr.county || '';
      const state = addr.state || '';
      const name  = r.display_name.split(',')[0].trim();
      const type  = r.type || r.class || 'place';
      return {
        osm_id:    r.osm_id,
        name,
        city,
        state,
        country:   addr.country || 'India',
        latitude:  parseFloat(r.lat),
        longitude: parseFloat(r.lon),
        type,
        category:  guessCategory(type, name),
        display_name: r.display_name,
        description: `${name} is a ${type} located in ${[city, state, 'India'].filter(Boolean).join(', ')}.`,
        rating:    '—',
        images:    [],
        entry_fee: 0,
        visit_duration: 'Varies',
      };
    });
  } catch (e) {
    console.error('Live search error:', e);
    return [];
  }
}


// ── Guess category from OSM type/name ────────────────
function guessCategory(type, name) {
  const t = (type + ' ' + name).toLowerCase();
  if (/beach|coast|bay|island/.test(t))         return 'beach';
  if (/mountain|peak|hill|valley|forest|lake|river|waterfall|national.park|wildlife|nature/.test(t)) return 'nature';
  if (/fort|palace|temple|mosque|church|monument|ruins|ancient|museum|tomb|heritage/.test(t)) return 'heritage';
  if (/hill.station|snow|trek|altitude/.test(t)) return 'hill';
  if (/city|town|market|downtown/.test(t))       return 'city';
  return 'heritage';
}


// ── Build card for stored place ───────────────────────
function buildPlaceCard(place, idx, isLive) {
  const catIcons = { heritage:'🏛️', nature:'🌿', beach:'🏖️', hill:'⛰️', city:'🏙️' };
  const imgHtml  = (place.images && place.images[0] && place.images[0].startsWith('http'))
    ? `<div class="place-card-img-bg" style="background-image:url('${place.images[0]}');background-size:cover;background-position:center"></div>`
    : `<div class="place-card-img-bg cat-${place.category}" style="display:flex;align-items:center;justify-content:center;font-size:3.5rem">${catIcons[place.category]||'📍'}</div>`;
  const fee = place.entry_fee === 0
    ? '<span class="place-fee free">Free Entry</span>'
    : `<span class="place-fee">₹${place.entry_fee} entry</span>`;

  return `
    <a href="/place/${place.id}" class="place-card" style="--delay:${idx * 0.05}s">
      <div class="place-card-image">
        ${imgHtml}
        <div class="place-card-overlay">
          <span class="place-category-badge">${escHtml(place.category)}</span>
        </div>
      </div>
      <div class="place-card-body">
        <div class="place-card-meta">
          <span class="place-city">📍 ${escHtml(place.city)}, ${escHtml(place.state)}</span>
          <span class="place-rating">⭐ ${place.rating}</span>
        </div>
        <h3 class="place-card-name">${escHtml(place.name)}</h3>
        <p class="place-card-desc">${escHtml((place.description || '').slice(0, 100))}…</p>
        <div class="place-card-footer">
          ${fee}
          <span class="place-duration">⏱ ${escHtml(place.visit_duration || '')}</span>
        </div>
      </div>
    </a>`;
}


// ── Build card for live OpenStreetMap result ─────────
function buildLiveCard(place, idx) {
  const catIcons = { heritage:'🏛️', nature:'🌿', beach:'🏖️', hill:'⛰️', city:'🏙️' };
  const icon     = catIcons[place.category] || '📍';
  const mapsUrl  = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.name + ' ' + place.state + ' India')}`;
  const wikiUrl  = `https://en.wikipedia.org/wiki/Special:Search?search=${encodeURIComponent(place.name)}`;

  return `
    <div class="place-card live-result" style="--delay:${idx * 0.05}s">
      <div class="place-card-image">
        <div class="place-card-img-bg cat-${place.category}"
             style="display:flex;align-items:center;justify-content:center;font-size:3.5rem;position:relative"
             id="liveImg_${idx}">
          ${icon}
        </div>
        <div class="place-card-overlay">
          <span class="place-category-badge">${escHtml(place.category)}</span>
          <span class="live-badge">🌍 Live Result</span>
        </div>
      </div>
      <div class="place-card-body">
        <div class="place-card-meta">
          <span class="place-city">📍 ${escHtml(place.city || place.state)}, ${escHtml(place.state)}</span>
          <span class="place-rating" style="color:#888;font-size:.75rem">${escHtml(place.type)}</span>
        </div>
        <h3 class="place-card-name">${escHtml(place.name)}</h3>
        <p class="place-card-desc">${escHtml(place.description.slice(0, 100))}…</p>
        <div class="place-card-footer" style="gap:6px;flex-wrap:wrap">
          <a href="${mapsUrl}" target="_blank" rel="noopener"
             onclick="event.stopPropagation()"
             style="font-size:.75rem;color:#1A73E8;font-weight:600;text-decoration:none">
            🗺 Maps
          </a>
          <a href="${wikiUrl}" target="_blank" rel="noopener"
             onclick="event.stopPropagation()"
             style="font-size:.75rem;color:#555;font-weight:600;text-decoration:none">
            📖 Wikipedia
          </a>
          <button onclick="addToApp(${JSON.stringify(place).replace(/"/g,'&quot;')}, this)"
                  style="margin-left:auto;font-size:.75rem;background:#C9A84C;color:white;border:none;padding:3px 10px;border-radius:6px;cursor:pointer;font-family:inherit">
            + Save
          </button>
        </div>
      </div>
    </div>`;
}


// ── Add live place to app database ───────────────────
async function addToApp(place, btn) {
  btn.textContent = 'Saving…';
  btn.disabled    = true;

  try {
    const res  = await fetch('/api/places/add', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        name:          place.name,
        city:          place.city,
        state:         place.state,
        country:       place.country || 'India',
        category:      place.category,
        description:   place.description,
        latitude:      place.latitude,
        longitude:     place.longitude,
        entry_fee:     0,
        visit_duration: 'Varies',
      })
    });
    const data = await res.json();

    if (res.ok && data.place) {
      btn.textContent = '✅ Saved!';
      btn.style.background = '#2D6A4F';
      // Replace the card with a proper stored card
      const card = btn.closest('.place-card');
      if (card) {
        card.outerHTML = buildPlaceCard(data.place, 0, false);
      }
    } else {
      btn.textContent = 'Retry';
      btn.disabled    = false;
    }
  } catch {
    btn.textContent = 'Retry';
    btn.disabled    = false;
  }
}


// ── UI Helpers ────────────────────────────────────────
function showSkeletons(grid) {
  grid.innerHTML = Array(6).fill(`
    <div class="place-card skeleton">
      <div class="place-card-image skeleton-img"></div>
      <div class="place-card-body">
        <div class="skeleton-line short"></div>
        <div class="skeleton-line long"></div>
        <div class="skeleton-line medium"></div>
      </div>
    </div>`).join('');
}

function emptyState(msg) {
  return `<div style="grid-column:1/-1;text-align:center;padding:60px 20px">
    <div style="font-size:3rem;margin-bottom:12px">🗺️</div>
    <h3 style="font-family:'Playfair Display',serif;margin-bottom:8px">No results found</h3>
    <p style="color:#888;font-size:.9rem">${msg}</p>
  </div>`;
}

function errorState() {
  return `<div style="grid-column:1/-1;text-align:center;padding:40px;color:#E74C3C">
    ⚠️ Failed to load places. Please check your connection and try again.
  </div>`;
}

function renderPagination(data) {
  const pagEl = document.getElementById('pagination');
  if (!pagEl || !data.pages || data.pages <= 1) {
    if (pagEl) pagEl.innerHTML = '';
    return;
  }
  let html = '';
  if (data.has_prev) html += `<button class="page-btn" onclick="goPage(${currentPage-1})">← Prev</button>`;
  for (let p = 1; p <= data.pages; p++) {
    html += `<button class="page-btn ${p===currentPage?'active':''}" onclick="goPage(${p})">${p}</button>`;
  }
  if (data.has_next) html += `<button class="page-btn" onclick="goPage(${currentPage+1})">Next →</button>`;
  pagEl.innerHTML = html;
}

function goPage(p) {
  currentPage = p;
  loadPlaces();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function escHtml(str) {
  return String(str || '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}
