// ===== MENU.JS - Restaurant & Food Menu Data with Real Images =====

const RESTAURANTS = [
  {
    id: 1, name: "Pizza Hub", cuisine: "Italian, Pizza, Pasta", rating: 4.5, deliveryTime: "30-40 min", minOrder: 200, freeDeliveryAbove: 500,
    img: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&h=300&fit=crop&auto=format",
    emoji: "🍕", discount: "50% OFF", tags: ["Trending", "Top Rated"]
  },
  {
    id: 2, name: "Burger House", cuisine: "American, Burgers, Fries", rating: 4.3, deliveryTime: "25-35 min", minOrder: 150, freeDeliveryAbove: 400,
    img: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&h=300&fit=crop&auto=format",
    emoji: "🍔", discount: "20% OFF", tags: ["Popular"]
  },
  {
    id: 3, name: "Biryani Palace", cuisine: "Indian, Biryani, Curry", rating: 4.7, deliveryTime: "40-50 min", minOrder: 250, freeDeliveryAbove: 600,
    img: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&h=300&fit=crop&auto=format",
    emoji: "🍛", discount: "30% OFF", tags: ["Best Seller", "Top Rated"]
  },
  {
    id: 4, name: "Food Express", cuisine: "Fast Food, Sandwiches, Wraps", rating: 4.1, deliveryTime: "20-30 min", minOrder: 100, freeDeliveryAbove: 350,
    img: "https://images.unsplash.com/photo-1553909489-cd47e0907980?w=600&h=300&fit=crop&auto=format",
    emoji: "🌯", discount: "15% OFF", tags: ["Quick Delivery"]
  },
  {
    id: 5, name: "Dragon Noodles", cuisine: "Chinese, Noodles, Dim Sum", rating: 4.4, deliveryTime: "35-45 min", minOrder: 200, freeDeliveryAbove: 500,
    img: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&h=300&fit=crop&auto=format",
    emoji: "🍜", discount: "25% OFF", tags: ["Trending"]
  },
  {
    id: 6, name: "South Spice", cuisine: "South Indian, Dosa, Idli", rating: 4.6, deliveryTime: "30-40 min", minOrder: 150, freeDeliveryAbove: 400,
    img: "https://images.unsplash.com/photo-1630383249896-424e482df921?w=600&h=300&fit=crop&auto=format",
    emoji: "🥘", discount: "10% OFF", tags: ["Healthy"]
  }
];

const FOOD_ITEMS = {
  1: [
    { id: 101, name: "Margherita Pizza", price: 299, desc: "Classic tomato, mozzarella & fresh basil", img: "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&h=220&fit=crop&auto=format", emoji: "🍕", type: "veg", rating: 4.5, popular: true },
    { id: 102, name: "Pepperoni Pizza", price: 399, desc: "Loaded with spicy pepperoni & cheese", img: "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400&h=220&fit=crop&auto=format", emoji: "🍕", type: "nonveg", rating: 4.6, popular: true },
    { id: 103, name: "BBQ Chicken Pizza", price: 449, desc: "Smoky BBQ sauce with grilled chicken", img: "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=220&fit=crop&auto=format", emoji: "🍕", type: "nonveg", rating: 4.4, popular: false },
    { id: 104, name: "Pasta Arrabiata", price: 249, desc: "Spicy tomato sauce with penne pasta", img: "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&h=220&fit=crop&auto=format", emoji: "🍝", type: "veg", rating: 4.2, popular: false },
    { id: 105, name: "Garlic Bread", price: 129, desc: "Crispy garlic bread with herb butter", img: "https://images.unsplash.com/photo-1619531040576-f9416740661b?w=400&h=220&fit=crop&auto=format", emoji: "🥖", type: "veg", rating: 4.3, popular: true },
    { id: 106, name: "Tiramisu", price: 189, desc: "Classic Italian coffee dessert", img: "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400&h=220&fit=crop&auto=format", emoji: "🍰", type: "veg", rating: 4.7, popular: false }
  ],
  2: [
    { id: 201, name: "Classic Beef Burger", price: 249, desc: "Juicy beef patty with lettuce & tomato", img: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=220&fit=crop&auto=format", emoji: "🍔", type: "nonveg", rating: 4.5, popular: true },
    { id: 202, name: "Veggie Burger", price: 179, desc: "Crispy veggie patty with fresh veggies", img: "https://images.unsplash.com/photo-1520072959219-c595dc870360?w=400&h=220&fit=crop&auto=format", emoji: "🍔", type: "veg", rating: 4.2, popular: false },
    { id: 203, name: "Crispy Chicken Burger", price: 219, desc: "Fried chicken fillet with spicy mayo", img: "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400&h=220&fit=crop&auto=format", emoji: "🍔", type: "nonveg", rating: 4.6, popular: true },
    { id: 204, name: "Cheese Fries", price: 149, desc: "Golden fries topped with melted cheese", img: "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&h=220&fit=crop&auto=format", emoji: "🍟", type: "veg", rating: 4.4, popular: true },
    { id: 205, name: "Onion Rings", price: 129, desc: "Crispy battered onion rings", img: "https://images.unsplash.com/photo-1639024471283-03518883512d?w=400&h=220&fit=crop&auto=format", emoji: "🧅", type: "veg", rating: 4.1, popular: false },
    { id: 206, name: "Chocolate Shake", price: 159, desc: "Rich creamy chocolate milkshake", img: "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400&h=220&fit=crop&auto=format", emoji: "🥤", type: "veg", rating: 4.5, popular: false }
  ],
  3: [
    { id: 301, name: "Chicken Biryani", price: 329, desc: "Aromatic basmati rice with spiced chicken", img: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&h=220&fit=crop&auto=format", emoji: "🍛", type: "nonveg", rating: 4.8, popular: true },
    { id: 302, name: "Mutton Biryani", price: 399, desc: "Tender mutton with fragrant spices", img: "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400&h=220&fit=crop&auto=format", emoji: "🍛", type: "nonveg", rating: 4.7, popular: true },
    { id: 303, name: "Veg Biryani", price: 249, desc: "Mixed vegetables in aromatic rice", img: "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=400&h=220&fit=crop&auto=format", emoji: "🍛", type: "veg", rating: 4.4, popular: false },
    { id: 304, name: "Butter Chicken", price: 299, desc: "Creamy tomato gravy with tender chicken", img: "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=400&h=220&fit=crop&auto=format", emoji: "🍗", type: "nonveg", rating: 4.6, popular: true },
    { id: 305, name: "Dal Makhani", price: 219, desc: "Slow cooked black lentils with butter", img: "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=220&fit=crop&auto=format", emoji: "🫘", type: "veg", rating: 4.5, popular: false },
    { id: 306, name: "Gulab Jamun", price: 99, desc: "Soft dumplings in rose sugar syrup", img: "https://images.unsplash.com/photo-1666350825571-e9ff4e4b4b41?w=400&h=220&fit=crop&auto=format", emoji: "🍮", type: "veg", rating: 4.7, popular: false }
  ],
  4: [
    { id: 401, name: "Club Sandwich", price: 199, desc: "Triple decker with chicken & veggies", img: "https://images.unsplash.com/photo-1553909489-cd47e0907980?w=400&h=220&fit=crop&auto=format", emoji: "🥪", type: "nonveg", rating: 4.3, popular: true },
    { id: 402, name: "Veggie Wrap", price: 169, desc: "Fresh veggies in whole wheat tortilla", img: "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400&h=220&fit=crop&auto=format", emoji: "🌯", type: "veg", rating: 4.2, popular: false },
    { id: 403, name: "Chicken Caesar Salad", price: 249, desc: "Grilled chicken with Caesar dressing", img: "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=220&fit=crop&auto=format", emoji: "🥗", type: "nonveg", rating: 4.4, popular: true },
    { id: 404, name: "French Fries", price: 119, desc: "Crispy golden salted fries", img: "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&h=220&fit=crop&auto=format", emoji: "🍟", type: "veg", rating: 4.3, popular: true },
    { id: 405, name: "Cold Coffee", price: 139, desc: "Iced coffee with cream & caramel", img: "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400&h=220&fit=crop&auto=format", emoji: "☕", type: "veg", rating: 4.5, popular: false },
    { id: 406, name: "Brownie", price: 129, desc: "Warm chocolate brownie with ice cream", img: "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400&h=220&fit=crop&auto=format", emoji: "🍫", type: "veg", rating: 4.6, popular: false }
  ],
  5: [
    { id: 501, name: "Veg Hakka Noodles", price: 199, desc: "Stir-fried noodles with vegetables", img: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=220&fit=crop&auto=format", emoji: "🍜", type: "veg", rating: 4.3, popular: true },
    { id: 502, name: "Chicken Noodles", price: 249, desc: "Wok tossed with chicken & soy sauce", img: "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&h=220&fit=crop&auto=format", emoji: "🍜", type: "nonveg", rating: 4.5, popular: true },
    { id: 503, name: "Veg Fried Rice", price: 179, desc: "Classic Chinese style fried rice", img: "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400&h=220&fit=crop&auto=format", emoji: "🍚", type: "veg", rating: 4.2, popular: false },
    { id: 504, name: "Chicken Manchurian", price: 279, desc: "Crispy chicken in tangy Manchurian sauce", img: "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400&h=220&fit=crop&auto=format", emoji: "🍗", type: "nonveg", rating: 4.6, popular: true },
    { id: 505, name: "Dim Sum Basket", price: 219, desc: "Steamed dumplings with dipping sauce", img: "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&h=220&fit=crop&auto=format", emoji: "🥟", type: "veg", rating: 4.4, popular: false },
    { id: 506, name: "Hot & Sour Soup", price: 149, desc: "Classic Chinese soup with vegetables", img: "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=220&fit=crop&auto=format", emoji: "🥣", type: "veg", rating: 4.3, popular: false }
  ],
  6: [
    { id: 601, name: "Masala Dosa", price: 139, desc: "Crispy dosa with spiced potato filling", img: "https://images.unsplash.com/photo-1630383249896-424e482df921?w=400&h=220&fit=crop&auto=format", emoji: "🥞", type: "veg", rating: 4.7, popular: true },
    { id: 602, name: "Idli Sambar", price: 99, desc: "Soft idlis with sambar & chutney", img: "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400&h=220&fit=crop&auto=format", emoji: "🍚", type: "veg", rating: 4.6, popular: true },
    { id: 603, name: "Medu Vada", price: 89, desc: "Crispy lentil donuts with coconut chutney", img: "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=400&h=220&fit=crop&auto=format", emoji: "🍩", type: "veg", rating: 4.4, popular: false },
    { id: 604, name: "Rava Uttapam", price: 119, desc: "Semolina pancake with onion & tomato", img: "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=220&fit=crop&auto=format", emoji: "🥞", type: "veg", rating: 4.3, popular: false },
    { id: 605, name: "Pongal", price: 109, desc: "Rice & lentil khichdi with ghee", img: "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=400&h=220&fit=crop&auto=format", emoji: "🍲", type: "veg", rating: 4.5, popular: false },
    { id: 606, name: "Filter Coffee", price: 59, desc: "Authentic South Indian filter coffee", img: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&h=220&fit=crop&auto=format", emoji: "☕", type: "veg", rating: 4.8, popular: true }
  ]
};

const PROMO_CODES = [
  { code: 'SAVE50', discount: 50, type: 'flat', minOrder: 300 },
  { code: 'WELCOME20', discount: 20, type: 'percent', minOrder: 200 },
  { code: 'FIRSTORDER', discount: 100, type: 'flat', minOrder: 500 },
  { code: 'SMARTFOOD', discount: 15, type: 'percent', minOrder: 150 }
];

const DELIVERY_AGENTS = [
  { id: 'DA001', name: 'Raj Kumar', phone: '9876543210', rating: 4.8 },
  { id: 'DA002', name: 'Suresh Nair', phone: '9876543211', rating: 4.6 },
  { id: 'DA003', name: 'Amit Singh', phone: '9876543212', rating: 4.9 },
  { id: 'DA004', name: 'Vijay Reddy', phone: '9876543213', rating: 4.7 }
];

// ===== RENDER FUNCTIONS WITH REAL IMAGES =====

function renderRestaurants(container, restaurants = RESTAURANTS) {
  container.innerHTML = '';
  restaurants.forEach(r => {
    const card = document.createElement('a');
    card.className = 'restaurant-card';
    card.href = `menu.html?restaurant=${r.id}`;
    card.innerHTML = `
      <div style="position:relative;height:180px;overflow:hidden;border-radius:16px 16px 0 0;">
        <img src="${r.img}" alt="${r.name}"
          style="width:100%;height:100%;object-fit:cover;transition:transform 0.45s ease;"
          onmouseover="this.style.transform='scale(1.07)'"
          onmouseout="this.style.transform='scale(1)'"
          onerror="this.src='https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&h=300&fit=crop'">
        <div style="position:absolute;inset:0;background:linear-gradient(to bottom,transparent 40%,rgba(0,0,0,0.45));"></div>
        ${r.discount ? `<span class="discount-badge">${r.discount}</span>` : ''}
      </div>
      <div class="restaurant-info">
        <div class="restaurant-name">${r.name}</div>
        <div class="restaurant-cuisine">${r.cuisine}</div>
        <div class="restaurant-meta">
          <span class="meta-item rating"><i class="fas fa-star"></i> ${r.rating}</span>
          <span class="meta-item"><i class="fas fa-clock"></i> ${r.deliveryTime}</span>
          <span class="meta-item"><i class="fas fa-rupee-sign"></i> ${r.minOrder} min</span>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function renderFoodItems(container, restaurantId) {
  const items = FOOD_ITEMS[restaurantId] || [];
  const cart = JSON.parse(localStorage.getItem('cart') || '[]');
  container.innerHTML = '';
  items.forEach(item => {
    const inCart = cart.find(c => c.id === item.id);
    const card = document.createElement('div');
    card.className = 'food-card';
    card.innerHTML = `
      <div style="position:relative;height:170px;overflow:hidden;border-radius:16px 16px 0 0;">
        <img src="${item.img}" alt="${item.name}"
          style="width:100%;height:100%;object-fit:cover;transition:transform 0.45s ease;"
          onmouseover="this.style.transform='scale(1.07)'"
          onmouseout="this.style.transform='scale(1)'"
          onerror="this.src='https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=220&fit=crop'">
        <span class="food-veg-badge ${item.type}" style="position:absolute;top:10px;left:10px;"></span>
        ${item.popular ? '<span style="position:absolute;top:10px;right:10px;background:rgba(252,128,25,0.92);color:white;font-size:0.7rem;font-weight:800;padding:3px 8px;border-radius:6px;backdrop-filter:blur(4px);">🔥 Hot</span>' : ''}
      </div>
      <div class="food-info">
        <div class="food-name">${item.name}</div>
        <div class="food-desc">${item.desc}</div>
        <div class="food-footer">
          <span class="food-price">₹${item.price}</span>
          <button class="add-btn ${inCart ? 'added' : ''}" onclick="addToCart(${item.id}, ${restaurantId})" id="add-btn-${item.id}">
            ${inCart ? `<i class="fas fa-check"></i> Added` : `+ ADD`}
          </button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Kept for backward compat
function getItemGradient() { return '#f5f5f5'; }

function addToCart(itemId, restaurantId) {
  if (!AUTH.isLoggedIn()) {
    window.location.href = 'login.html';
    return;
  }
  const item = (FOOD_ITEMS[restaurantId] || []).find(f => f.id === itemId);
  if (!item) return;
  const restaurant = RESTAURANTS.find(r => r.id === restaurantId);
  let cart = JSON.parse(localStorage.getItem('cart') || '[]');

  if (cart.length > 0 && cart[0].restaurantId !== restaurantId) {
    if (!confirm('Your cart has items from another restaurant. Clear cart and add this item?')) return;
    cart = [];
  }

  const existing = cart.find(c => c.id === itemId);
  if (existing) {
    existing.quantity += 1;
  } else {
    cart.push({ ...item, restaurantId, restaurantName: restaurant.name, quantity: 1 });
  }

  localStorage.setItem('cart', JSON.stringify(cart));
  AUTH.updateCartCount();

  const btn = document.getElementById(`add-btn-${itemId}`);
  if (btn) { btn.classList.add('added'); btn.innerHTML = '<i class="fas fa-check"></i> Added'; }
  TOAST.show(`${item.name} added to cart!`, 'success');
}
