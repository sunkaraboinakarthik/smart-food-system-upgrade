// ===== API.JS - Central API client for the SmartFood backend =====
// Change API_BASE if you deploy the backend somewhere other than localhost:5000
const API_BASE = window.SMARTFOOD_API_BASE || 'http://localhost:5000/api';

const API = {
  token() {
    return localStorage.getItem('sf_token') || '';
  },

  async request(path, { method = 'GET', body, auth = true, isForm = false } = {}) {
    const headers = {};
    if (!isForm) headers['Content-Type'] = 'application/json';
    if (auth && this.token()) headers['Authorization'] = `Bearer ${this.token()}`;

    let res;
    try {
      res = await fetch(`${API_BASE}${path}`, {
        method,
        headers,
        body: body ? (isForm ? body : JSON.stringify(body)) : undefined,
      });
    } catch (e) {
      throw { success: false, message: 'Cannot reach SmartFood server. Is the backend running on ' + API_BASE + '?' };
    }

    let data;
    try { data = await res.json(); } catch (e) { data = { success: false, message: 'Invalid server response' }; }

    if (!res.ok) throw data;
    return data;
  },

  get(path)          { return this.request(path); },
  post(path, body)   { return this.request(path, { method: 'POST', body }); },
  put(path, body)    { return this.request(path, { method: 'PUT', body }); },
  patch(path, body)  { return this.request(path, { method: 'PATCH', body }); },
  del(path)          { return this.request(path, { method: 'DELETE' }); },
};
