/* frontend/static/js/login.js */
document.addEventListener('DOMContentLoaded', () => {
  loadHeader();
  const form = document.getElementById('login-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append('username', form.username.value);
    fd.append('password', form.password.value);
    try {
      const res = await fetch('/auth/login', { method: 'POST', body: fd });
      const data = await res.json();
      if (!res.ok) throw data;
      setToken(data.access_token);
      location.href = '/pages/sessions.html';
    } catch (err) {
      console.error(err);
      showToast(err?.detail || 'Error en login', 'error');
    }
  });
});
