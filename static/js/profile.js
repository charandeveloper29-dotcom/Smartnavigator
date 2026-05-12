/* ═══════════════════════════════════════════
   Smart Navigator — profile.js
   Profile editing and logout
   ═══════════════════════════════════════════ */

function toggleEditMode() {
  const form     = document.getElementById('editProfileForm');
  const nameEl   = document.getElementById('profileName');
  const editName = document.getElementById('editName');
  if (!form) return;

  const editing = form.hidden;
  form.hidden   = !editing;
  if (editing && editName && nameEl) {
    editName.value = nameEl.textContent.trim();
    editName.focus();
  }
}

async function saveProfile() {
  const name    = document.getElementById('editName').value.trim();
  const msgEl   = document.getElementById('editMsg');
  const nameEl  = document.getElementById('profileName');

  if (!name) { if (msgEl) msgEl.textContent = 'Name cannot be empty'; return; }

  const res  = await fetch('/api/profile', {
    method:  'PUT',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ name }),
    credentials: 'same-origin'
  });
  const data = await res.json();

  if (res.ok) {
    if (nameEl) nameEl.textContent = name;
    toggleEditMode();
    // Update navbar avatar letter
    const avatar = document.querySelector('.nav-avatar .avatar-letter');
    if (avatar) avatar.textContent = name[0].toUpperCase();
  } else {
    if (msgEl) msgEl.textContent = data.error || 'Update failed';
  }
}

function confirmLogout() {
  if (!confirm('Are you sure you want to sign out?')) return;
  fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' })
    .then(() => window.location.href = '/');
}


/* ── Avatar Upload ─────────────────────────── */
async function uploadAvatar(input) {
  const file = input.files[0];
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) { alert('Image must be under 5MB'); return; }

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64 = e.target.result;
    const ext    = file.name.split('.').pop();

    // Show preview immediately
    const imgEl = document.getElementById('profileAvatarImg');
    const letEl = document.getElementById('profileAvatarLetter');
    if (imgEl) imgEl.src = base64;
    else if (letEl) {
      const wrap = letEl.parentElement;
      const newImg = document.createElement('img');
      newImg.id  = 'profileAvatarImg';
      newImg.src = base64;
      newImg.style.cssText = 'width:72px;height:72px;border-radius:50%;object-fit:cover;border:3px solid white';
      letEl.replaceWith(newImg);
    }
    // Update navbar avatar
    const navAv = document.querySelector('.nav-avatar');
    if (navAv) {
      const navImg = document.createElement('img');
      navImg.src = base64;
      navImg.style.cssText = 'width:100%;height:100%;object-fit:cover;border-radius:50%';
      navAv.innerHTML = '';
      navAv.appendChild(navImg);
    }

    const res  = await fetch('/api/profile/avatar', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data: base64, ext })
    });
    const data = await res.json();
    if (!res.ok) alert('Upload failed: ' + (data.error || 'Unknown error'));
  };
  reader.readAsDataURL(file);
}

/* ── Bio Edit ──────────────────────────────── */
function toggleBioEdit() {
  const wrap = document.getElementById('bioEditWrap');
  const disp = document.getElementById('bioDisplay');
  const open = wrap.style.display === 'none';
  wrap.style.display = open ? 'block' : 'none';
  disp.style.display = open ? 'none' : '';
  if (open) document.getElementById('bioInput').focus();
}

async function saveBio() {
  const bio  = document.getElementById('bioInput').value.trim();
  const disp = document.getElementById('bioDisplay');
  const res  = await fetch('/api/profile/bio', {
    method: 'PUT', credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bio })
  });
  if (res.ok) {
    disp.textContent = bio || '+ Add a bio about yourself…';
    disp.style.fontStyle = bio ? 'normal' : 'italic';
    toggleBioEdit();
  }
}
