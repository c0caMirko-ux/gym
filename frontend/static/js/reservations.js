/* frontend/static/js/reservations.js */
document.addEventListener('DOMContentLoaded', async () => {
  loadHeader();
  const container = document.getElementById('my-reservations');
  try {
    const rows = await apiFetch('/me/reservations');
    if (!rows || !rows.length) { container.textContent = 'No tienes reservas.'; return; }
    container.innerHTML = '';
    rows.forEach(r => {
      const el = document.createElement('div');
      el.className = 'reservation';
      el.innerHTML = `
        <h3>${escapeHtml(r.session.class_type_title || 'Clase')}</h3>
        <p>${new Date(r.session.start_time).toLocaleString()} - ${new Date(r.session.end_time).toLocaleString()}</p>
        <p>Estado: ${r.status}</p>
        <button data-id="${r.id}" class="btn cancel-btn">Cancelar</button>
      `;
      container.appendChild(el);
    });
    container.addEventListener('click', async (ev) => {
      const btn = ev.target.closest('.cancel-btn');
      if (!btn) return;
      const id = btn.dataset.id;
      if (!confirm('Confirmas cancelar esta reserva?')) return;
      try {
        await apiFetch(`/reservations/${id}/cancel`, { method: 'PATCH' });
        showToast('Reserva cancelada', 'success');
        location.reload();
      } catch (err) {
        console.error(err);
        showToast(err?.data?.detail || 'Error al cancelar', 'error');
      }
    });
  } catch (err) {
    console.error(err);
    container.textContent = 'Error cargando reservas';
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
