/* frontend/static/js/register.js */
document.addEventListener('DOMContentLoaded', () => {
  loadHeader();
  const form = document.getElementById('register-form');
  if (!form) return;
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
      full_name: form.full_name.value.trim(),
      email: form.email.value.trim(),
      password: form.password.value
    };
    try {
      const res = await apiFetch('/auth/register', { method: 'POST', body: data });
      setToken(res.access_token);
      showToast('Registro exitoso', 'success');
      location.href = '/pages/sessions.html';
    } catch (err) {
      console.error(err);
      showToast(err?.data?.detail || 'Error en registro', 'error');
    }
  });
});
