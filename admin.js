// ===== ADMIN.JS - Admin Dashboard wired to the real SmartFood API =====

let revenueChartInstance = null;
let currentOrders = [];
let agentsCache = [];

async function initAdminDashboard() {
  if (!AUTH.requireAdmin()) return;
  await Promise.all([loadStats(), loadOrders(), loadAgents()]);
}

async function loadStats() {
  try {
    const res = await API.get('/admin/stats');
    const s = res.data;
    document.getElementById('totalOrders').textContent = s.total_orders;
    document.getElementById('activeOrders').textContent =
      s.pending_orders + s.preparing_orders + s.out_for_delivery_orders;
    document.getElementById('totalRevenue').textContent = '₹' + s.total_revenue.toLocaleString();
    document.getElementById('totalUsers').textContent = s.total_users;
    document.getElementById('onlineUsers').textContent = s.online_users;
    document.getElementById('todayRegs').textContent = s.today_registrations;
    document.getElementById('pendingOrders').textContent = s.pending_orders;
    document.getElementById('preparingOrders').textContent = s.preparing_orders;
    document.getElementById('outForDeliveryOrders').textContent = s.out_for_delivery_orders;
    document.getElementById('deliveredOrders').textContent = s.delivered_orders;
    document.getElementById('cancelledOrders').textContent = s.cancelled_orders;
    document.getElementById('todayRevenue').textContent = '₹' + s.today_revenue.toLocaleString();
    document.getElementById('monthlyRevenue').textContent = '₹' + s.monthly_revenue.toLocaleString();

    renderRevenueChart(s.revenue_chart);

    // Seed the live feed with recent activity on first load
    const feed = document.getElementById('liveFeed');
    if (feed && !feed.dataset.loaded) {
      feed.innerHTML = s.recent_activity.map(renderFeedItem).join('') ||
        '<div style="color:var(--text-light);padding:10px;">No activity yet</div>';
      feed.dataset.loaded = '1';
    }
  } catch (e) {
    TOAST.show(e.message || 'Failed to load dashboard stats', 'error');
  }
}

function renderRevenueChart(data) {
  const ctx = document.getElementById('revenueChart');
  if (!ctx || typeof Chart === 'undefined') return;
  const labels = data.map(d => d.date);
  const values = data.map(d => d.revenue);
  if (revenueChartInstance) revenueChartInstance.destroy();
  revenueChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: values,
        borderColor: '#FC8019',
        backgroundColor: 'rgba(252,128,25,0.15)',
        fill: true,
        tension: 0.35,
      }]
    },
    options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
  });
}

function renderFeedItem(item) {
  const icons = {
    register: '🆕', login: '🔓', logout: '🔒', cart_add: '🛒', cart_remove: '🗑️',
    order_placed: '📦', payment_success: '💳', order_status_update: '🚚', order_cancelled: '❌',
  };
  const icon = icons[item.action] || '🔔';
  return `<div style="padding:8px 0;border-bottom:1px solid var(--border);">
    <div><strong>${item.user_name || 'System'}</strong> ${icon} <span style="color:var(--text-light);">${item.action.replace(/_/g,' ')}</span></div>
    <div style="color:var(--text-light);font-size:0.78rem;">${item.details || ''} · ${item.created_at}</div>
  </div>`;
}

function connectLiveFeed() {
  if (typeof io === 'undefined') return; // socket.io not loaded
  const socket = io(API_BASE.replace('/api', ''));
  socket.on('connect', () => {
    socket.emit('join_admin');
    const dot = document.getElementById('liveDot');
    if (dot) dot.style.background = '#60b246';
  });
  socket.on('disconnect', () => {
    const dot = document.getElementById('liveDot');
    if (dot) dot.style.background = '#ccc';
  });
  socket.on('activity', (item) => {
    const feed = document.getElementById('liveFeed');
    if (!feed) return;
    feed.insertAdjacentHTML('afterbegin', renderFeedItem(item));
    while (feed.children.length > 40) feed.removeChild(feed.lastChild);
  });
  socket.on('online_count', (data) => {
    const el = document.getElementById('onlineUsers');
    if (el) el.textContent = data.online_users;
  });
  socket.on('notification', (n) => {
    TOAST.show(`🔔 ${n.title}`, n.type === 'error' ? 'error' : n.type === 'warning' ? 'warning' : 'info');
  });
}

async function loadAgents() {
  try {
    const res = await API.get('/admin/agents');
    agentsCache = res.data;
  } catch (e) { /* non-fatal */ }
}

async function loadOrders() {
  const tbody = document.getElementById('ordersTableBody');
  tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-light);">Loading...</td></tr>`;
  try {
    const res = await API.get('/orders/all');
    currentOrders = res.data;
    renderOrdersTable(currentOrders);
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--danger);">${e.message || 'Failed to load orders'}</td></tr>`;
  }
}

function renderOrdersTable(orders) {
  const tbody = document.getElementById('ordersTableBody');
  if (!tbody) return;

  if (!orders.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--text-light);">No orders found</td></tr>`;
    return;
  }

  tbody.innerHTML = orders.map(order => `
    <tr>
      <td><strong>#${order.id}</strong></td>
      <td>${order.user_name}</td>
      <td>${(order.items || []).map(i => `${i.emoji || ''} ${i.name} ×${i.quantity}`).join(', ').substring(0, 50)}</td>
      <td><strong>₹${order.total}</strong></td>
      <td><span class="status-badge ${getStatusClass(order.status)}">${order.status}</span></td>
      <td>${order.agent_name || '<span style="color:var(--text-light)">Unassigned</span>'}</td>
      <td>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <select class="form-select" onchange="updateOrderStatus(${order.id}, this.value)">
            <option value="">Status...</option>
            ${['Pending','Preparing','Picked Up','On The Way','Delivered','Cancelled'].map(s => `<option value="${s}" ${order.status === s ? 'selected' : ''}>${s}</option>`).join('')}
          </select>
          <select class="form-select" onchange="assignAgent(${order.id}, this.value)">
            <option value="">Assign Agent</option>
            ${agentsCache.map(a => `<option value="${a.agent_code}" ${order.agent_id === a.agent_code ? 'selected' : ''}>${a.name}</option>`).join('')}
          </select>
        </div>
      </td>
    </tr>
  `).join('');
}

async function updateOrderStatus(orderId, status) {
  if (!status) return;
  try {
    await API.patch(`/orders/${orderId}/status`, { status });
    TOAST.show(`Order #${orderId} status updated to "${status}"`, 'success');
    await loadOrders();
    await loadStats();
  } catch (e) {
    TOAST.show(e.message || 'Failed to update status', 'error');
  }
}

async function assignAgent(orderId, agentCode) {
  if (!agentCode) return;
  try {
    await API.patch(`/orders/${orderId}/assign`, { agent_code: agentCode });
    TOAST.show('Delivery agent assigned', 'success');
    await loadOrders();
  } catch (e) {
    TOAST.show(e.message || 'Failed to assign agent', 'error');
  }
}

function getStatusClass(status) {
  const map = {
    'Pending': 'badge-pending',
    'Preparing': 'badge-preparing',
    'Picked Up': 'badge-picked',
    'On The Way': 'badge-onway',
    'Delivered': 'badge-delivered',
    'Cancelled': 'badge-cancelled'
  };
  return map[status] || 'badge-pending';
}

function filterOrders(status) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  if (window.event && window.event.target) window.event.target.classList.add('active');
  const filtered = status === 'all' ? currentOrders : currentOrders.filter(o => o.status === status);
  renderOrdersTable(filtered);
}
