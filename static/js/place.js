/* ═══════════════════════════════════════════
   Smart Navigator — place.js
   Nearby places loader, route filter
   ═══════════════════════════════════════════ */

// PLACE_ID, PLACE_LAT, PLACE_LNG are injected inline in place.html

document.addEventListener('DOMContentLoaded', () => {
  loadNearby(20);
});

// ─── Load Nearby Places ───────────────────
async function loadNearby(radius) {
  const loadingEl = document.getElementById('nearbyLoading');
  const cardsEl   = document.getElementById('nearbyCards');
  const emptyEl   = document.getElementById('nearbyEmpty');

  if (!cardsEl) return;

  loadingEl.style.display = 'flex';
  cardsEl.innerHTML = '';
  if (emptyEl) emptyEl.hidden = true;

  try {
    const res  = await fetch(`/api/places/${PLACE_ID}/nearby?radius=${radius}&limit=10`);
    const data = await res.json();
    loadingEl.style.display = 'none';

    if (!data.places || data.places.length === 0) {
      if (emptyEl) emptyEl.hidden = false;
      return;
    }

    cardsEl.innerHTML = data.places.map(p => buildNearbyCard(p)).join('');
  } catch (err) {
    loadingEl.style.display = 'none';
    cardsEl.innerHTML = '<p style="color:#888;padding:16px">Could not load nearby places.</p>';
  }
}

function buildNearbyCard(place) {
  const catIcons = { heritage:'🏛️', nature:'🌿', beach:'🏖️', hill:'⛰️', city:'🏙️' };
  const icon = catIcons[place.category] || '📍';
  const fee  = place.entry_fee === 0 ? 'Free' : `₹${place.entry_fee}`;

  return `
    <a href="/place/${place.id}" class="nearby-card">
      <div class="nearby-card-img cat-${place.category}" style="display:flex;align-items:center;justify-content:center;font-size:2.5rem">
        ${icon}
      </div>
      <div class="nearby-card-body">
        <div class="nearby-card-name" title="${escHtml(place.name)}">${escHtml(place.name)}</div>
        <div class="nearby-card-info">
          <span>⭐ ${place.rating}</span>
          <span class="nearby-distance">📍 ${place.distance_formatted}</span>
        </div>
        <div style="font-size:.75rem;color:#888;margin-top:3px">${escHtml(place.city)}</div>
      </div>
    </a>`;
}

// ─── Utilities ────────────────────────────
function escHtml(str) {
  return String(str || '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}
