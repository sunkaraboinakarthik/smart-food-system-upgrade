// ===== ORDERS.JS - Order Management =====

const ORDERS = {
  getOrders() {
    return JSON.parse(localStorage.getItem('orders') || '[]');
  },

  saveOrders(orders) {
    localStorage.setItem('orders', JSON.stringify(orders));
  },

  createOrder(paymentMethod) {
    const user = AUTH.getLoggedInUser();
    const cart = CART.getCart();
    if (!cart.length || !user) return null;

    const order = {
      id: Date.now(),
      userId: user.id,
      userName: user.name,
      userAddress: user.address,
      items: cart,
      subtotal: CART.getSubtotal(),
      deliveryFee: CART.getDeliveryFee(CART.getSubtotal()),
      discount: CART.getDiscount(),
      total: CART.getTotal(),
      paymentMethod,
      status: 'Pending',
      agentId: null,
      agentName: null,
      restaurantName: cart[0]?.restaurantName || '',
      createdAt: new Date().toISOString(),
      statusHistory: [{ status: 'Pending', time: new Date().toISOString() }]
    };

    const orders = this.getOrders();
    orders.unshift(order);
    this.saveOrders(orders);

    // Clear cart
    CART.clearCart();
    localStorage.removeItem('promoDiscount');
    localStorage.removeItem('appliedPromo');

    return order;
  },

  updateStatus(orderId, status, agentId = null, agentName = null) {
    const orders = this.getOrders();
    const order = orders.find(o => o.id == orderId);
    if (!order) return false;

    order.status = status;
    if (agentId) { order.agentId = agentId; order.agentName = agentName; }
    order.statusHistory.push({ status, time: new Date().toISOString() });
    this.saveOrders(orders);
    return true;
  },

  getOrderById(orderId) {
    return this.getOrders().find(o => o.id == orderId);
  },

  getUserOrders(userId) {
    return this.getOrders().filter(o => o.userId == userId);
  },

  getAgentOrders(agentId) {
    return this.getOrders().filter(o => o.agentId === agentId);
  }
};

// Status order for progress
const STATUS_STEPS = ['Pending', 'Preparing', 'Picked Up', 'On The Way', 'Delivered'];
const STATUS_ICONS = { 'Pending': 'fa-clock', 'Preparing': 'fa-fire', 'Picked Up': 'fa-box', 'On The Way': 'fa-motorcycle', 'Delivered': 'fa-check-circle' };

function renderTrackOrder(orderId) {
  const order = ORDERS.getOrderById(orderId);
  const container = document.getElementById('trackContainer');
  if (!container) return;

  if (!order) {
    container.innerHTML = `<div class="empty-state"><span class="empty-icon">🔍</span><h3>Order Not Found</h3><p>We couldn't find this order. Please check the order ID.</p><a href="index.html" class="checkout-btn" style="display:inline-block;width:auto;padding:12px 28px;">Go Home</a></div>`;
    return;
  }

  const currentStep = STATUS_STEPS.indexOf(order.status);

  container.innerHTML = `
    <div class="track-layout">
      <div>
        <div class="track-card mb-20">
          <h3 style="font-family:var(--font-display);font-weight:800;margin-bottom:6px;">Order #${order.id}</h3>
          <p style="color:var(--text-light);font-size:0.88rem;">${new Date(order.createdAt).toLocaleString()}</p>
          <div class="status-timeline" style="margin-top:24px;">
            ${STATUS_STEPS.map((step, i) => `
              <div class="status-step ${i < currentStep ? 'done' : ''} ${i === currentStep ? 'active' : ''}">
                <div class="step-icon"><i class="fas ${STATUS_ICONS[step]}"></i></div>
                <div class="step-content">
                  <h4>${step}</h4>
                  <p>${getStatusDesc(step)}</p>
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="track-card">
          <h3 style="font-family:var(--font-display);font-weight:700;margin-bottom:16px;">Order Items</h3>
          ${order.items.map(item => `
            <div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border);">
              <span>${item.emoji} ${item.name} × ${item.quantity}</span>
              <span style="font-weight:700;">₹${item.price * item.quantity}</span>
            </div>
          `).join('')}
          <div style="display:flex;justify-content:space-between;margin-top:12px;font-weight:800;font-size:1.05rem;">
            <span>Total</span><span style="color:var(--primary);">₹${order.total}</span>
          </div>
        </div>
      </div>

      <div>
        <div class="track-card mb-20">
          <h3 style="font-family:var(--font-display);font-weight:700;margin-bottom:16px;">Delivery Details</h3>
          <div style="display:flex;flex-direction:column;gap:12px;">
            <div style="display:flex;gap:12px;align-items:flex-start;">
              <i class="fas fa-map-marker-alt" style="color:var(--primary);margin-top:2px;"></i>
              <div><div style="font-weight:700;font-size:0.85rem;">Delivering To</div><div style="color:var(--text-mid);font-size:0.9rem;">${order.userAddress || 'Not specified'}</div></div>
            </div>
            ${order.agentName ? `
            <div style="display:flex;gap:12px;align-items:center;">
              <i class="fas fa-user" style="color:var(--primary);"></i>
              <div><div style="font-weight:700;font-size:0.85rem;">Delivery Agent</div><div style="color:var(--text-mid);font-size:0.9rem;">${order.agentName}</div></div>
            </div>` : `<div style="color:var(--text-light);font-size:0.88rem;">Agent will be assigned shortly</div>`}
          </div>
        </div>

        <div class="track-card">
          <h3 style="font-family:var(--font-display);font-weight:700;margin-bottom:16px;">Payment Info</h3>
          <div class="summary-row"><span>Subtotal</span><span>₹${order.subtotal}</span></div>
          <div class="summary-row"><span>Delivery</span><span>${order.deliveryFee === 0 ? 'FREE' : '₹' + order.deliveryFee}</span></div>
          ${order.discount > 0 ? `<div class="summary-row"><span>Discount</span><span style="color:var(--accent)">-₹${order.discount}</span></div>` : ''}
          <div class="summary-row total"><span>Total Paid</span><span>₹${order.total}</span></div>
          <div style="margin-top:10px;font-size:0.85rem;color:var(--text-light);"><i class="fas fa-credit-card"></i> ${order.paymentMethod}</div>
        </div>
      </div>
    </div>
  `;
}

function getStatusDesc(status) {
  const map = {
    'Pending': 'Your order has been placed',
    'Preparing': 'Restaurant is preparing your food',
    'Picked Up': 'Delivery agent picked up your order',
    'On The Way': 'Your order is on the way',
    'Delivered': 'Order delivered successfully!'
  };
  return map[status] || '';
}
