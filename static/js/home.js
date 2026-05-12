/* ═══════════════════════════════════════════
   Smart Navigator — home.js
   Search autocomplete + Cost calculator
   ═══════════════════════════════════════════ */

// ─── Autocomplete Search ──────────────────
(function () {
  const searchInput = document.getElementById('homeSearch');
  const dropdown = document.getElementById('autocompleteDropdown');
  const submitBtn = document.getElementById('searchSubmit');
  if (!searchInput) return;

  let debounceTimer;

  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = searchInput.value.trim();
    if (!q) { hideDropdown(); return; }
    debounceTimer = setTimeout(() => fetchSuggestions(q), 280);
  });

  searchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      const q = searchInput.value.trim();
      if (q) window.location.href = `/search?q=${encodeURIComponent(q)}`;
    }
    if (e.key === 'Escape') hideDropdown();
  });

  if (submitBtn) {
    submitBtn.addEventListener('click', () => {
      const q = searchInput.value.trim();
      if (q) window.location.href = `/search?q=${encodeURIComponent(q)}`;
    });
  }

  document.addEventListener('click', e => {
    if (!e.target.closest('#searchBar')) hideDropdown();
  });

  async function fetchSuggestions(q) {
    try {
      const res = await fetch(`/api/places/search?q=${encodeURIComponent(q)}`);
      const places = await res.json();
      renderDropdown(places, q);
    } catch { hideDropdown(); }
  }

  function renderDropdown(places, query) {
    if (!places.length) { hideDropdown(); return; }
    const html = places.map(p => `
      <a class="autocomplete-item" href="/place/${p.id}">
        <span class="ac-icon">${CAT_ICONS[p.category] || '📍'}</span>
        <div class="ac-info">
          <div class="ac-name">${highlight(p.name, query)}</div>
          <div class="ac-location">${p.city}, ${p.state}</div>
        </div>
        <span class="ac-rating">⭐ ${p.rating}</span>
      </a>`).join('');
    dropdown.innerHTML = html;
    dropdown.hidden = false;
  }

  function highlight(text, query) {
    const re = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')})`, 'gi');
    return text.replace(re, '<strong>$1</strong>');
  }

  function hideDropdown() { dropdown.hidden = true; dropdown.innerHTML = ''; }
})();

// ─── Cost Calculator ──────────────────────
const TRAVEL_COSTS = {
  flight: { budget: 3500, mid: 6000, luxury: 12000 },
  train:  { budget: 400,  mid: 1200, luxury: 2800  },
  bus:    { budget: 300,  mid: 700,  luxury: 1500  },
  cab:    { budget: 2000, mid: 4000, luxury: 8000  }
};
const HOTEL_COSTS = {
  budget: 1500, mid: 5000, luxury: 18000
};
const FOOD_COSTS = {
  budget: 400, mid: 1000, luxury: 2500
};

function calculateCost() {
  const mode   = document.getElementById('calcMode').value;
  const people = +document.getElementById('calcPeople').value;
  const days   = +document.getElementById('calcDays').value;
  const budget = document.getElementById('calcBudget').value;

  if (!people || !days || people < 1 || days < 1) {
    alert('Please enter valid number of people and days.');
    return;
  }

  const travelCost = (TRAVEL_COSTS[mode][budget] || 0) * people;
  const hotelCost  = HOTEL_COSTS[budget] * days;
  const foodCost   = FOOD_COSTS[budget] * people * days;
  const miscCost   = Math.round((travelCost + hotelCost + foodCost) * 0.1);
  const total      = travelCost + hotelCost + foodCost + miscCost;

  const modeLabels = { flight:'✈️ Flight', train:'🚂 Train', bus:'🚌 Bus', cab:'🚕 Cab' };
  const budgetLabels = { budget:'Budget', mid:'Mid-range', luxury:'Luxury' };

  const html = `
    <h3>Estimated Trip Cost</h3>
    <div class="calc-breakdown">
      <div class="calc-item">
        <span class="calc-item-label">${modeLabels[mode]} (${people} pax)</span>
        <span class="calc-item-value">₹${fmt(travelCost)}</span>
      </div>
      <div class="calc-item">
        <span class="calc-item-label">🏨 Hotel (${days} nights)</span>
        <span class="calc-item-value">₹${fmt(hotelCost)}</span>
      </div>
      <div class="calc-item">
        <span class="calc-item-label">🍽️ Food (${days} days)</span>
        <span class="calc-item-value">₹${fmt(foodCost)}</span>
      </div>
      <div class="calc-item">
        <span class="calc-item-label">🎟️ Misc / Entry</span>
        <span class="calc-item-value">₹${fmt(miscCost)}</span>
      </div>
    </div>
    <div class="calc-total">
      <span class="calc-total-label">Total (${budgetLabels[budget]} · ${people} people · ${days} days)</span>
      <span class="calc-total-value">₹${fmt(total)}</span>
    </div>
  `;

  const resultEl = document.getElementById('calcResult');
  resultEl.innerHTML = html;
  resultEl.hidden = false;
  resultEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function fmt(n) {
  return n.toLocaleString('en-IN');
}
