const API_ROOT = window.API_ROOT || ''

export async function apiFetch(path, { method = 'GET', token, body } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (token === undefined) token = localStorage.getItem('api_token') || ''
  if (token) headers['Authorization'] = 'Bearer ' + token
  try {
    const res = await fetch(API_ROOT + path, { method, headers, body: body ? JSON.stringify(body) : undefined })
    const text = await res.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (e) { data = text }
    return { ok: res.ok, status: res.status, data }
  } catch (err) {
    // Network error or CORS error — don't throw, return structured failure
    return { ok: false, status: 0, data: { detail: err.message || 'Network error' } }
  }
}

export default apiFetch
