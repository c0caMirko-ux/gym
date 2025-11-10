/* frontend/static/js/ui.js */
async function loadHeader() {
  try {
    const r = await fetch('/static/components/header.html');
    if (r.ok) {
      const html = await r.text();
      const container = document.getElementById('header-container');
      if (container) container.innerHTML = html;
      const logoutBtn = document.getElementById('logout-btn');
      const token = localStorage.getItem('access_token');
      if (logoutBtn) {
        logoutBtn.style.display = token ? 'inline-block' : 'none';
        logoutBtn.addEventListener('click', () => {
          clearToken();
          location.href = '/pages/login.html';
        });
      }
    }
  } catch (e) {
    // ignore silently
    console.debug('header load failed', e);
  }
}

function showToast(msg, type='info') {
  // Fallback simple
  alert(msg);
}
