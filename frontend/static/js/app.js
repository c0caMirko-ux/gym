/* frontend/static/js/app.js */
// Helper central para llamadas a la API y manejo de token
const API_BASE = ''; // si UI y API están en el mismo host, dejar vacío

function setToken(token) { localStorage.setItem('access_token', token); }
function getToken() { return localStorage.getItem('access_token'); }
function clearToken() { localStorage.removeItem('access_token'); }

async function apiFetch(path, options = {}) {
  const headers = options.headers ? {...options.headers} : {};
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const fetchOptions = { ...options, headers };

  // Si el body es un objeto (no FormData ni string), convertir a JSON
  if (fetchOptions.body && !(fetchOptions.body instanceof FormData) && typeof fetchOptions.body === 'object') {
    fetchOptions.body = JSON.stringify(fetchOptions.body);
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(API_BASE + path, fetchOptions);
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch(e){ data = text; }
  if (!res.ok) throw { status: res.status, data };
  return data;
}
