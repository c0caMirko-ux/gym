/* frontend/static/js/sessions.js */
document.addEventListener('DOMContentLoaded', async () => {
  loadHeader();
  const container = document.getElementById('sessions-list');
  try {
    const sessions = await apiFetch('/sessions');
    if (!sessions || !sessions.length) { container.textContent = 'No hay sesiones.'; return; }
    container.innerHTML = '';
    sessions.forEach(s => {
      const el = document.createElement('article');
      el.className = 'card';
      const start = s.start_time ? new Date(s.start_time).toLocaleString() : '—';
      const end = s.end_time ? new Date(s.end_time).toLocaleString() : '—';
      const title = (s.class_type && s.class_type.title) ? s.class_type.title : 'Clase';
      el.innerHTML = `
        <h3>${escapeHtml(title)}</h3>
        <p>${start} — ${end}</p>
        <p>Capacidad: ${s.capacity ?? '—'}</p>
        <a href="/pages/session.html?id=${s.id}" class="btn">Ver / Reservar</a>
      `;
      container.appendChild(el);
    });
  } catch (err) {
    console.error(err);
    container.textContent = 'Error cargando sesiones';
  }
});

function escapeHtml(unsafe) {
  if (!unsafe || typeof unsafe !== 'string') return unsafe;
  return unsafe
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}
