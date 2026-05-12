/* Smart Navigator — splash.js: Real language switching + ribbon */

document.addEventListener('DOMContentLoaded', async () => {
  initLanguageSelector();
  await loadRibbon();
});

function initLanguageSelector() {
  const buttons = document.querySelectorAll('.lang-btn');
  const saved   = localStorage.getItem('sn_lang') || 'en';
  buttons.forEach(b => b.classList.toggle('active', b.dataset.lang === saved));
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      buttons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      applyTranslation(btn.dataset.lang);
    });
  });
  applyTranslation(saved);
}

async function loadRibbon() {
  const track = document.getElementById('ribbonTrack');
  if (!track) return;
  try {
    const res    = await fetch('/api/places?per_page=12');
    const data   = await res.json();
    const places = data.items || [];
    if (!places.length) return;
    const catIcons = { heritage:'🏛️', nature:'🌿', beach:'🏖️', hill:'⛰️', city:'🏙️' };
    const html = [...places, ...places].map(p => `
      <a href="/place/${p.id}" class="ribbon-place-chip">
        <span class="rpc-icon">${escHtml(p.category) in catIcons ? catIcons[p.category] : '📍'}</span>
        <div>
          <div class="rpc-name">${escHtml(p.name)}</div>
          <div class="rpc-location">${escHtml(p.city)}, ${escHtml(p.state)}</div>
        </div>
        <span class="rpc-rating">⭐ ${p.rating}</span>
      </a>`).join('');
    track.innerHTML = html;
  } catch (err) { console.error('[Ribbon]', err); }
}

function escHtml(str) {
  return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
