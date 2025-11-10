/* frontend/static/js/ui.js */
async function loadHeader() {
  try {
    const r = await fetch('/static/components/header.html');
    if (r.ok) {
      const html = await r.text();
      document.getElementById('header-container').innerHTML = html;
      // hook logout
      const logoutBtn = document.getElementById('logout-btn');
      if (logoutBtn) logoutBtn.addEventListener('click', () => { clearToken(); location.href = '/pages/login.html'; });
    }
  } catch (e) { /* ignore */ }
}

function showToast(msg, type='info') {
  // simple alert fallback; puedes mejorar con un toast DOM
  alert(msg);
}