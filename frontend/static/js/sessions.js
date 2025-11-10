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
      el.innerHTML = `
        <h3>${s.class_type?.title || 'Clase'}</h3>
        <p>${new Date(s.start_time).toLocaleString()} - ${new Date(s.end_time).toLocaleString()}</p>
        <p>Capacidad: ${s.capacity}</p>
        <a href="/pages/session.html?id=${s.id}" class="btn">Ver / Reservar</a>
      `;
      container.appendChild(el);
    });
  } catch (err) {
    console.error(err);
    container.textContent = 'Error cargando sesiones';
  }
});
