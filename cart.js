// ===== CART.JS - Cart Management =====

const CART = {
  getCart() {
    return JSON.parse(localStorage.getItem('cart') || '[]');
  },

  saveCart(cart) {
    localStorage.setItem('cart', JSON.stringify(cart));
    AUTH.updateCartCount();
  },

  updateQuantity(itemId, delta) {
    let cart = this.getCart();
    const item = cart.find(c => c.id === itemId);
    if (!item) return;
    item.quantity += delta;
    if (item.quantity <= 0) cart = cart.filter(c => c.id !== itemId);
    this.saveCart(cart);
    renderCartPage();
  },

  removeItem(itemId) {
    let cart = this.getCart().filter(c => c.id !== itemId);
    this.saveCart(cart);
    renderCartPage();
    TOAST.show('Item removed from cart', 'info');
  },

  clearCart() {
    localStorage.removeItem('cart');
    AUTH.updateCartCount();
  },

  getSubtotal() {
    return this.getCart().reduce((sum, item) => sum + (item.price * item.quantity), 0);
  },

  getDeliveryFee(subtotal) {
    return subtotal >= 500 ? 0 : 40;
  },

  getDiscount() {
    return parseFloat(localStorage.getItem('promoDiscount') || '0');
  },

  getTotal() {
    const sub = this.getSubtotal();
    const delivery = this.getDeliveryFee(sub);
    const discount = this.getDiscount();
    return Math.max(0, sub + delivery - discount);
  }
};

function renderCartPage() {
  const cart = CART.getCart();
  const cartItemsEl = document.getElementById('cartItems');
  const emptyEl = document.getElementById('emptyCart');
  const summaryEl = document.getElementById('cartSummary');

  if (!cartItemsEl) return;

  if (cart.length === 0) {
    if (emptyEl) emptyEl.style.display = 'block';
    if (summaryEl) summaryEl.style.display = 'none';
    cartItemsEl.innerHTML = '';
    return;
  }

  if (emptyEl) emptyEl.style.display = 'none';
  if (summaryEl) summaryEl.style.display = 'block';

  cartItemsEl.innerHTML = '';
  cart.forEach(item => {
    const div = document.createElement('div');
    div.className = 'cart-item';
    div.innerHTML = `
      <div class="cart-item-img" style="overflow:hidden;border-radius:12px;padding:0;">
        <img src="${item.img || ''}" alt="${item.name}"
          style="width:80px;height:80px;object-fit:cover;border-radius:12px;"
          onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
        <div style="display:none;width:80px;height:80px;background:#f5f5f5;border-radius:12px;align-items:center;justify-content:center;font-size:28px;">${item.emoji}</div>
      </div>
      <div class="cart-item-info">
        <div class="cart-item-name">${item.name}</div>
        <div class="cart-item-restaurant">${item.restaurantName}</div>
        <div class="cart-item-price">₹${item.price * item.quantity}</div>
      </div>
      <div class="qty-control">
        <button class="qty-btn" onclick="CART.updateQuantity(${item.id}, -1)">−</button>
        <span class="qty-display">${item.quantity}</span>
        <button class="qty-btn" onclick="CART.updateQuantity(${item.id}, 1)">+</button>
      </div>
      <button class="remove-btn" onclick="CART.removeItem(${item.id})" title="Remove">
        <i class="fas fa-trash"></i>
      </button>
    `;
    cartItemsEl.appendChild(div);
  });

  updateCartSummary();
}

function updateCartSummary() {
  const sub = CART.getSubtotal();
  const delivery = CART.getDeliveryFee(sub);
  const discount = CART.getDiscount();
  const total = CART.getTotal();

  const el = (id) => document.getElementById(id);
  if (el('subtotal')) el('subtotal').textContent = `₹${sub}`;
  if (el('deliveryFee')) el('deliveryFee').textContent = delivery === 0 ? 'FREE' : `₹${delivery}`;
  if (el('discountRow')) el('discountRow').style.display = discount > 0 ? 'flex' : 'none';
  if (el('discountAmount')) el('discountAmount').textContent = `-₹${discount}`;
  if (el('totalAmount')) el('totalAmount').textContent = `₹${total}`;
}

// Promo code validation
function applyPromoCode() {
  const code = document.getElementById('promoInput')?.value?.trim()?.toUpperCase();
  const msgEl = document.getElementById('promoMsg');
  if (!code) return;

  const promo = PROMO_CODES.find(p => p.code === code);
  const subtotal = CART.getSubtotal();

  if (!promo) {
    msgEl.textContent = '❌ Invalid promo code';
    msgEl.className = 'promo-msg error';
    localStorage.removeItem('promoDiscount');
  } else if (subtotal < promo.minOrder) {
    msgEl.textContent = `❌ Minimum order ₹${promo.minOrder} required`;
    msgEl.className = 'promo-msg error';
    localStorage.removeItem('promoDiscount');
  } else {
    const discount = promo.type === 'flat' ? promo.discount : Math.round(subtotal * promo.discount / 100);
    localStorage.setItem('promoDiscount', discount);
    localStorage.setItem('appliedPromo', code);
    msgEl.textContent = `✅ Promo applied! Saved ₹${discount}`;
    msgEl.className = 'promo-msg success';
    TOAST.show(`Promo code applied! You saved ₹${discount}`, 'success');
    updateCartSummary();
  }
}
