/* ═══════════════════════════════════════════
   Smart Navigator — auth.js
   Login and registration form logic
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm    = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');

  if (loginForm)    loginForm.addEventListener('submit', handleLogin);
  if (registerForm) registerForm.addEventListener('submit', handleRegister);
});

// ─── Login ────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  clearErrors();

  const email    = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;
  const btn      = document.getElementById('loginBtn');

  if (!email)    { setErr('loginEmailErr', 'Email is required'); return; }
  if (!password) { setErr('loginPwdErr',   'Password is required'); return; }

  setLoading(btn, true);

  const res = await fetch('/api/auth/login', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ email, password }),
    credentials: 'same-origin'
  });

  const data = await res.json();
  setLoading(btn, false);

  if (res.ok) {
    showAlert('success', '✅ Welcome back! Redirecting…');
    setTimeout(() => window.location.href = '/home', 800);
  } else {
    showAlert('error', data.error || 'Login failed. Please try again.');
    document.getElementById('loginPassword').value = '';
  }
}

// ─── Register ─────────────────────────────
async function handleRegister(e) {
  e.preventDefault();
  clearErrors();

  const name     = document.getElementById('regName').value.trim();
  const email    = document.getElementById('regEmail').value.trim();
  const password = document.getElementById('regPassword').value;
  const btn      = document.getElementById('regBtn');

  let valid = true;
  if (!name)  { setErr('nameErr',  'Full name is required'); valid = false; }
  if (!email) { setErr('emailErr', 'Email is required');     valid = false; }
  else if (!email.includes('@')) { setErr('emailErr', 'Enter a valid email'); valid = false; }
  if (!password) { setErr('pwdErr', 'Password is required'); valid = false; }
  else if (password.length < 6) { setErr('pwdErr', 'Min. 6 characters'); valid = false; }
  if (!valid) return;

  setLoading(btn, true);

  const res = await fetch('/api/auth/register', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ name, email, password }),
    credentials: 'same-origin'
  });

  const data = await res.json();
  setLoading(btn, false);

  if (res.ok) {
    showAlert('success', '🎉 Account created! Redirecting…');
    setTimeout(() => window.location.href = '/home', 900);
  } else {
    showAlert('error', data.error || 'Registration failed. Please try again.');
  }
}

// ─── Helpers ──────────────────────────────
function setErr(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg;
}

function clearErrors() {
  document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
  const alertEl = document.getElementById('formAlert');
  if (alertEl) { alertEl.hidden = true; alertEl.textContent = ''; }
}

function showAlert(type, msg) {
  const alertEl = document.getElementById('formAlert');
  if (!alertEl) return;
  alertEl.textContent = msg;
  alertEl.className   = `form-alert ${type}`;
  alertEl.hidden      = false;
}

function setLoading(btn, loading) {
  if (!btn) return;
  const label  = btn.querySelector('span:not(.btn-loader)');
  const loader = btn.querySelector('.btn-loader');
  btn.disabled = loading;
  if (label)  label.style.display = loading ? 'none' : '';
  if (loader) loader.hidden        = !loading;
}

function togglePwd(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const show = input.type === 'password';
  input.type  = show ? 'text' : 'password';
  btn.textContent = show ? '🙈' : '👁';
}
