// ===== AUTH.JS - Authentication client wired to the real SmartFood API =====

const AUTH = {
  init() {
    this.updateNavbar();
    this.updateCartCount();
  },

  getUser() {
    return JSON.parse(localStorage.getItem('sf_user') || 'null');
  },

  // Backward-compatible alias used by cart.html, dashboard.html, delivery-dashboard.html,
  // track-order.html, chatbot.js, delivery.js, orders.js
  getLoggedInUser() {
    return this.getUser();
  },

  setSession(user, token) {
    localStorage.setItem('sf_user', JSON.stringify(user));
    localStorage.setItem('sf_token', token);
  },

  isLoggedIn() {
    return !!this.getUser() && !!API.token();
  },

  async register(payload) {
    try {
      const res = await API.post('/auth/register', payload);
      return { success: true, data: res.data, message: res.message };
    } catch (e) {
      return { success: false, message: e.message || 'Registration failed' };
    }
  },

  async verifyEmailOtp(email, otp) {
    try {
      const res = await API.post('/auth/verify-email-otp', { email, otp });
      this.setSession(res.data.user, res.data.token);
      return { success: true, data: res.data };
    } catch (e) {
      return { success: false, message: e.message || 'Invalid OTP' };
    }
  },

  async resendOtp(email, purpose = 'email_verify') {
    try {
      await API.post('/auth/resend-otp', { email, purpose });
      return { success: true };
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  async login(identifier, password, remember = false) {
    const isEmail = identifier.includes('@');
    const payload = { password, remember };
    if (isEmail) payload.email = identifier.trim().toLowerCase();
    else payload.phone = identifier.trim();

    try {
      const res = await API.post('/auth/login', payload);
      this.setSession(res.data.user, res.data.token);
      return { success: true, data: res.data };
    } catch (e) {
      return { success: false, message: e.message || 'Login failed', otp_required: e.otp_required };
    }
  },

  async logout() {
    try { await API.post('/auth/logout'); } catch (e) { /* ignore network errors on logout */ }
    localStorage.removeItem('sf_user');
    localStorage.removeItem('sf_token');
    window.location.href = 'index.html';
  },

  async forgotPassword(email) {
    try {
      const res = await API.post('/auth/forgot-password', { email });
      return { success: true, message: res.message };
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  async resetPassword(email, otp, newPassword) {
    try {
      const res = await API.post('/auth/reset-password', { email, otp, newPassword });
      return { success: true, message: res.message };
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  updateNavbar() {
    const user = this.getUser();
    const loginBtn = document.getElementById('loginBtn');
    const userMenu = document.getElementById('userMenu');
    const userNameEl = document.getElementById('userName');
    const dashBtn = document.getElementById('dashBtn');

    if (user && loginBtn) {
      loginBtn.style.display = 'none';
      if (userMenu) {
        userMenu.style.display = 'flex';
        if (userNameEl) userNameEl.textContent = user.name.split(' ')[0];
      }
      if (dashBtn) dashBtn.style.display = 'flex';
    } else if (loginBtn) {
      loginBtn.style.display = 'flex';
      if (userMenu) userMenu.style.display = 'none';
      if (dashBtn) dashBtn.style.display = 'none';
    }
  },

  updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const count = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartCountEl = document.getElementById('cartCount');
    if (cartCountEl) {
      cartCountEl.textContent = count;
      cartCountEl.style.display = count > 0 ? 'flex' : 'none';
    }
  },

  requireLogin() {
    if (!this.isLoggedIn()) {
      window.location.href = 'login.html?redirect=' + encodeURIComponent(window.location.href);
      return false;
    }
    return true;
  },

  requireAdmin() {
    const user = this.getUser();
    if (!user || user.role !== 'admin') {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  },

  requireDelivery() {
    const user = this.getUser();
    if (!user || (user.role !== 'delivery' && user.role !== 'admin')) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  }
};

// Toast Notification System
const TOAST = {
  show(message, type = 'info', duration = 3000) {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const icons = { success: '✅', error: '❌', info: '🔔', warning: '⚠️' };
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${icons[type] || '🔔'}</span> ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = 'slideInToast 0.3s ease reverse';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  AUTH.init();
});
