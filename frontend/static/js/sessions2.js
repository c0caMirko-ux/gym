/* frontend/static/js/session.js */
document.addEventListener('DOMContentLoaded', async () => {
  loadHeader();
  const params = new URLSearchParams(location.search);
  const id = params.get('id');
  const container = document.getElementById('session-detail');
  if (!id) { container.textContent = 'ID de sesión faltante'; return; }
  try {
    // Si backend tiene GET /sessions/{id}, úsalo:
    let s = null;
    try {
      s = await apiFetch(`/sessions2/${id}`);
    } catch (e) {
      // fallback: obtener todas y buscar (para compatibilidad)
      const sessions = await apiFetch('/sessions2');
      s = sessions.find(x => x.id === id);
    }
    if (!s) { container.textContent = 'Sesión no encontrada'; return; }
    container.innerHTML = `
      <h2>${s.class_type?.title || 'Clase'}</h2>
      <p>${new Date(s.start_time).toLocaleString()} - ${new Date(s.end_time).toLocaleString()}</p>
      <p>Capacidad: ${s.capacity}</p>
      <button id="reserve-btn" class="btn">Reservar</button>
      <div id="reserve-result"></div>
    `;
    document.getElementById('reserve-btn').addEventListener('click', async () => {
      try {
        const res = await apiFetch('/reservations', {
          method: 'POST',
          body: JSON.stringify({ session_id: id, auto_waitlist: false })
        });
        showToast('Reservado con éxito', 'success');
        document.getElementById('reserve-result').textContent = JSON.stringify(res);
      } catch (err) {
        console.error(err);
        showToast(err?.data?.detail || 'Error al reservar', 'error');
      }
    });
  } catch (err) {
    console.error(err);
    container.textContent = 'Error cargando detalle';
  }
});
/* frontend/static/js/session.js */
document.addEventListener('DOMContentLoaded', async () => {
  loadHeader();
  const params = new URLSearchParams(location.search);
  const id = params.get('id');
  const container = document.getElementById('session-detail');
  if (!id) { container.textContent = 'ID de sesión faltante'; return; }
  try {
    // Si backend tiene GET /sessions/{id}, úsalo:
    let s = null;
    try {
      s = await apiFetch(`/sessions2/${id}`);
    } catch (e) {
      // fallback: obtener todas y buscar (para compatibilidad)
      const sessions = await apiFetch('/sessions2');
      s = sessions.find(x => x.id === id);
    }
    if (!s) { container.textContent = 'Sesión no encontrada'; return; }
    container.innerHTML = `
      <h2>${s.class_type?.title || 'Clase'}</h2>
      <p>${new Date(s.start_time).toLocaleString()} - ${new Date(s.end_time).toLocaleString()}</p>
      <p>Capacidad: ${s.capacity}</p>
      <button id="reserve-btn" class="btn">Reservar</button>
      <div id="reserve-result"></div>
    `;
    document.getElementById('reserve-btn').addEventListener('click', async () => {
      try {
        const res = await apiFetch('/reservations', {
          method: 'POST',
          body: JSON.stringify({ session_id: id, auto_waitlist: false })
        });
        showToast('Reservado con éxito', 'success');
        document.getElementById('reserve-result').textContent = JSON.stringify(res);
      } catch (err) {
        console.error(err);
        showToast(err?.data?.detail || 'Error al reservar', 'error');
      }
    });
  } catch (err) {
    console.error(err);
    container.textContent = 'Error cargando detalle';
  }
});
