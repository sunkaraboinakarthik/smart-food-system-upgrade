// ===== THEME.JS - Dark / Light mode toggle =====
const THEME = {
  KEY: 'sf_theme',

  init() {
    const saved = localStorage.getItem(this.KEY) || 'light';
    this.apply(saved);
  },

  apply(mode) {
    document.documentElement.setAttribute('data-theme', mode);
    localStorage.setItem(this.KEY, mode);
    const icon = document.getElementById('themeIcon');
    if (icon) icon.className = mode === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
  },

  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    this.apply(current === 'dark' ? 'light' : 'dark');
  },
};

document.addEventListener('DOMContentLoaded', () => THEME.init());
