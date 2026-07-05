// ===== DELIVERY.JS - Delivery Agent Dashboard =====

function initDeliveryDashboard() {
  if (!AUTH.requireDelivery()) return;
  const user = AUTH.getLoggedInUser();
  renderDeliveryOrders(user);
}

function renderDeliveryOrders(user) {
  const allOrders = ORDERS.getOrders();
  // For demo: show orders matching agent by name or all if admin
  const orders = user.role === 'admin'
    ? allOrders
    : allOrders.filter(o => o.agentName === user.name || o.agentId === 'DA001');

  const tbody = document.getElementById('deliveryTableBody');
  if (!tbody) return;

  // Update stats
  const assigned = orders.filter(o => o.status !== 'Delivered').length;
  const delivered = orders.filter(o => o.status === 'Delivered').length;
  if (document.getElementById('assignedCount')) document.getElementById('assignedCount').textContent = assigned;
  if (document.getElementById('deliveredCount')) document.getElementById('deliveredCount').textContent = delivered;
  if (document.getElementById('pendingCount')) document.getElementById('pendingCount').textContent = orders.filter(o => o.status === 'Pending' || o.status === 'Preparing').length;
  if (document.getElementById('earningsAmount')) document.getElementById('earningsAmount').textContent = '₹' + (delivered * 40).toLocaleString();

  tbody.innerHTML = '';

  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--text-light);"><span style="font-size:40px;display:block;margin-bottom:12px;">📦</span>No orders assigned yet</td></tr>`;
    return;
  }

  const DELIVERY_STATUSES = ['Preparing', 'Picked Up', 'On The Way', 'Delivered'];

  orders.forEach(order => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>#${order.id.toString().slice(-6)}</strong></td>
      <td>
        <div style="font-weight:700;">${order.userName}</div>
        <div style="font-size:0.8rem;color:var(--text-light);">${order.userAddress || 'No address'}</div>
      </td>
      <td>${order.restaurantName}</td>
      <td>${order.items.map(i => `${i.emoji} ${i.name}`).join(', ').substring(0, 40)}${order.items.length > 1 ? '...' : ''}</td>
      <td><span class="status-badge ${getStatusClass(order.status)}">${order.status}</span></td>
      <td>
        ${order.status !== 'Delivered' ? `
        <select class="form-select" onchange="updateDeliveryStatus(${order.id}, this.value)">
          <option value="">Update Status</option>
          ${DELIVERY_STATUSES.map(s => `<option value="${s}" ${order.status === s ? 'selected' : ''}>${s}</option>`).join('')}
        </select>` : `<span style="color:var(--accent);font-weight:700;font-size:0.85rem;">✅ Completed</span>`}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function updateDeliveryStatus(orderId, status) {
  if (!status) return;
  const user = AUTH.getLoggedInUser();
  ORDERS.updateStatus(orderId, status);
  TOAST.show(`Order marked as "${status}"`, 'success');
  renderDeliveryOrders(user);
}
