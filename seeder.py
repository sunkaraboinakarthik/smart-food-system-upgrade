"""
SmartFood Database Seeder
Populates all tables with demo data on first run
"""
from database import get_db
from auth_utils import hash_password


def seed():
    conn = get_db()
    c = conn.cursor()

    # ── Skip if already seeded ────────────────────────────────────────────────
    if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return

    print("\n📦 Seeding database...")

    # ── Users ─────────────────────────────────────────────────────────────────
    users = [
        ("Admin User",   "admin@smartfood.com",    hash_password("admin123"),    "admin",    "9000000001", "SmartFood HQ, Tech Park, Bangalore"),
        ("Ravi Kumar",   "delivery@smartfood.com", hash_password("delivery123"), "delivery", "9000000002", "Agent Base, MG Road, Bangalore"),
        ("Priya Sharma", "user@smartfood.com",     hash_password("user123"),     "user",     "9000000003", "123 Koramangala, Bangalore"),
    ]
    c.executemany(
        "INSERT INTO users(name,email,password,role,phone,address,email_verified,country_code) VALUES(?,?,?,?,?,?,1,'+91')",
        users
    )
    print(f"  ✓ {len(users)} users (demo accounts pre-verified)")

    # ── Restaurants ───────────────────────────────────────────────────────────
    restaurants = [
        ("Pizza Hub",      "Italian, Pizza, Pasta",        4.5, "30-40 min", 200,
         "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&h=300&fit=crop", "🍕", "50% OFF"),
        ("Burger House",   "American, Burgers, Fries",     4.3, "25-35 min", 150,
         "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&h=300&fit=crop", "🍔", "20% OFF"),
        ("Biryani Palace", "Indian, Biryani, Curry",       4.7, "40-50 min", 250,
         "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&h=300&fit=crop", "🍛", "30% OFF"),
        ("Food Express",   "Fast Food, Sandwiches, Wraps", 4.1, "20-30 min", 100,
         "https://images.unsplash.com/photo-1553909489-cd47e0907980?w=600&h=300&fit=crop",    "🌯", "15% OFF"),
        ("Dragon Noodles", "Chinese, Noodles, Dim Sum",    4.4, "35-45 min", 200,
         "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&h=300&fit=crop", "🍜", "25% OFF"),
        ("South Spice",    "South Indian, Dosa, Idli",     4.6, "30-40 min", 150,
         "https://images.unsplash.com/photo-1630383249896-424e482df921?w=600&h=300&fit=crop", "🥘", "10% OFF"),
    ]
    c.executemany(
        "INSERT INTO restaurants(name,cuisine,rating,delivery_time,min_order,img,emoji,discount) VALUES(?,?,?,?,?,?,?,?)",
        restaurants
    )
    print(f"  ✓ {len(restaurants)} restaurants")

    # Get restaurant IDs by name
    def rid(name):
        return c.execute("SELECT id FROM restaurants WHERE name=?", (name,)).fetchone()[0]

    # ── Food Items ─────────────────────────────────────────────────────────────
    items = [
        # name, price, desc, img, emoji, type, category, popular, restaurant
        # Pizza Hub
        ("Margherita Pizza",    299, "Classic tomato, mozzarella & fresh basil",   "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?w=400&h=220&fit=crop",   "🍕","veg",    "Pizza",    1, "Pizza Hub"),
        ("Pepperoni Pizza",     399, "Loaded with spicy pepperoni & cheese",       "https://images.unsplash.com/photo-1628840042765-356cda07504e?w=400&h=220&fit=crop",   "🍕","nonveg", "Pizza",    1, "Pizza Hub"),
        ("BBQ Chicken Pizza",   449, "Smoky BBQ sauce with grilled chicken",       "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400&h=220&fit=crop",   "🍕","nonveg", "Pizza",    0, "Pizza Hub"),
        ("Pasta Arrabiata",     249, "Spicy tomato sauce with penne pasta",        "https://images.unsplash.com/photo-1563379926898-05f4575a45d8?w=400&h=220&fit=crop",   "🍝","veg",    "Pasta",    0, "Pizza Hub"),
        ("Garlic Bread",        129, "Crispy garlic bread with herb butter",       "https://images.unsplash.com/photo-1619531040576-f9416740661b?w=400&h=220&fit=crop",   "🥖","veg",    "Sides",    1, "Pizza Hub"),
        ("Tiramisu",            189, "Classic Italian coffee dessert",             "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400&h=220&fit=crop",   "🍰","veg",    "Dessert",  0, "Pizza Hub"),
        # Burger House
        ("Classic Beef Burger", 249, "Juicy beef patty with lettuce & tomato",    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=220&fit=crop",   "🍔","nonveg", "Burger",   1, "Burger House"),
        ("Veggie Burger",       179, "Crispy veggie patty with fresh veggies",    "https://images.unsplash.com/photo-1520072959219-c595dc870360?w=400&h=220&fit=crop",   "🍔","veg",    "Burger",   0, "Burger House"),
        ("Crispy Chicken Burger",219,"Fried chicken fillet with spicy mayo",      "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=400&h=220&fit=crop",   "🍔","nonveg", "Burger",   1, "Burger House"),
        ("Cheese Fries",        149, "Golden fries topped with melted cheese",    "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&h=220&fit=crop",   "🍟","veg",    "Sides",    1, "Burger House"),
        ("Onion Rings",         129, "Crispy battered onion rings",               "https://images.unsplash.com/photo-1639024471283-03518883512d?w=400&h=220&fit=crop",   "🧅","veg",    "Sides",    0, "Burger House"),
        ("Chocolate Shake",     159, "Rich creamy chocolate milkshake",           "https://images.unsplash.com/photo-1572490122747-3968b75cc699?w=400&h=220&fit=crop",   "🥤","veg",    "Drinks",   0, "Burger House"),
        # Biryani Palace
        ("Chicken Biryani",     329, "Aromatic basmati rice with spiced chicken", "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&h=220&fit=crop",   "🍛","nonveg", "Biryani",  1, "Biryani Palace"),
        ("Mutton Biryani",      399, "Tender mutton with fragrant spices",        "https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400&h=220&fit=crop",   "🍛","nonveg", "Biryani",  1, "Biryani Palace"),
        ("Veg Biryani",         249, "Mixed vegetables in aromatic rice",         "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=400&h=220&fit=crop",   "🍛","veg",    "Biryani",  0, "Biryani Palace"),
        ("Butter Chicken",      299, "Creamy tomato gravy with tender chicken",   "https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=400&h=220&fit=crop",   "🍗","nonveg", "Curry",    1, "Biryani Palace"),
        ("Dal Makhani",         219, "Slow cooked black lentils with butter",     "https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&h=220&fit=crop",     "🫘","veg",    "Curry",    0, "Biryani Palace"),
        ("Gulab Jamun",          99, "Soft dumplings in rose sugar syrup",        "https://images.unsplash.com/photo-1666350825571-e9ff4e4b4b41?w=400&h=220&fit=crop",   "🍮","veg",    "Dessert",  0, "Biryani Palace"),
        # Food Express
        ("Club Sandwich",       199, "Triple decker with chicken & veggies",      "https://images.unsplash.com/photo-1553909489-cd47e0907980?w=400&h=220&fit=crop",      "🥪","nonveg", "Sandwich", 1, "Food Express"),
        ("Veggie Wrap",         169, "Fresh veggies in whole wheat tortilla",     "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=400&h=220&fit=crop",   "🌯","veg",    "Wrap",     0, "Food Express"),
        ("Caesar Salad",        249, "Grilled chicken with Caesar dressing",      "https://images.unsplash.com/photo-1546793665-c74683f339c1?w=400&h=220&fit=crop",     "🥗","nonveg", "Salad",    1, "Food Express"),
        ("French Fries",        119, "Crispy golden salted fries",               "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400&h=220&fit=crop",   "🍟","veg",    "Sides",    1, "Food Express"),
        ("Cold Coffee",         139, "Iced coffee with cream & caramel",         "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400&h=220&fit=crop",   "☕","veg",    "Drinks",   0, "Food Express"),
        ("Brownie",             129, "Warm chocolate brownie with ice cream",     "https://images.unsplash.com/photo-1564355808539-22fda35bed7e?w=400&h=220&fit=crop",   "🍫","veg",    "Dessert",  0, "Food Express"),
        # Dragon Noodles
        ("Veg Hakka Noodles",   199, "Stir-fried noodles with vegetables",       "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400&h=220&fit=crop",   "🍜","veg",    "Noodles",  1, "Dragon Noodles"),
        ("Chicken Noodles",     249, "Wok tossed with chicken & soy sauce",      "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=400&h=220&fit=crop",   "🍜","nonveg", "Noodles",  1, "Dragon Noodles"),
        ("Veg Fried Rice",      179, "Classic Chinese style fried rice",         "https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400&h=220&fit=crop",   "🍚","veg",    "Rice",     0, "Dragon Noodles"),
        ("Chicken Manchurian",  279, "Crispy chicken in tangy Manchurian sauce", "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400&h=220&fit=crop",   "🍗","nonveg", "Starters", 1, "Dragon Noodles"),
        ("Dim Sum Basket",      219, "Steamed dumplings with dipping sauce",     "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&h=220&fit=crop",     "🥟","veg",    "Starters", 0, "Dragon Noodles"),
        ("Hot & Sour Soup",     149, "Classic Chinese soup with vegetables",     "https://images.unsplash.com/photo-1547592166-23ac45744acd?w=400&h=220&fit=crop",     "🥣","veg",    "Soup",     0, "Dragon Noodles"),
        # South Spice
        ("Masala Dosa",         139, "Crispy dosa with spiced potato filling",   "https://images.unsplash.com/photo-1630383249896-424e482df921?w=400&h=220&fit=crop",   "🥞","veg",    "Dosa",     1, "South Spice"),
        ("Idli Sambar",          99, "Soft idlis with sambar & chutney",         "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400&h=220&fit=crop",   "🍚","veg",    "Breakfast",1, "South Spice"),
        ("Medu Vada",            89, "Crispy lentil donuts with coconut chutney","https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=400&h=220&fit=crop",   "🍩","veg",    "Snacks",   0, "South Spice"),
        ("Rava Uttapam",        119, "Semolina pancake with onion & tomato",     "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&h=220&fit=crop",   "🥞","veg",    "Breakfast",0, "South Spice"),
        ("Pongal",              109, "Rice & lentil khichdi with ghee",          "https://images.unsplash.com/photo-1645177628172-a94c1f96e6db?w=400&h=220&fit=crop",   "🍲","veg",    "Breakfast",0, "South Spice"),
        ("Filter Coffee",        59, "Authentic South Indian filter coffee",     "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400&h=220&fit=crop",   "☕","veg",    "Drinks",   1, "South Spice"),
    ]
    for (name, price, desc, img, emoji, typ, category, popular, rest_name) in items:
        restaurant_id = rid(rest_name)
        c.execute(
            "INSERT INTO food_items(restaurant_id,name,price,description,img,emoji,type,category,is_popular) VALUES(?,?,?,?,?,?,?,?,?)",
            (restaurant_id, name, price, desc, img, emoji, typ, category, popular)
        )
    print(f"  ✓ {len(items)} food items")

    # ── Promo Codes ───────────────────────────────────────────────────────────
    promos = [
        ("SAVE50",     "flat",    50,  300, "Flat ₹50 off on orders above ₹300",  "2025-12-31"),
        ("WELCOME20",  "percent", 20,  200, "20% off on orders above ₹200",       "2025-12-31"),
        ("FIRSTORDER", "flat",    100, 500, "₹100 off for new users (min ₹500)",  "2025-12-31"),
        ("SMARTFOOD",  "percent", 15,  150, "15% off sitewide",                   "2025-12-31"),
    ]
    c.executemany(
        "INSERT INTO promo_codes(code,type,value,min_order,description,expires_at) VALUES(?,?,?,?,?,?)",
        promos
    )
    print(f"  ✓ {len(promos)} promo codes")

    # ── Delivery Agents ───────────────────────────────────────────────────────
    agents = [
        ("DA001", "Raj Kumar",   "9876543210", 4.8),
        ("DA002", "Suresh Nair", "9876543211", 4.6),
        ("DA003", "Amit Singh",  "9876543212", 4.9),
        ("DA004", "Vijay Reddy", "9876543213", 4.7),
    ]
    c.executemany(
        "INSERT INTO delivery_agents(agent_code,name,phone,rating) VALUES(?,?,?,?)",
        agents
    )
    print(f"  ✓ {len(agents)} delivery agents")

    # ── Inventory ─────────────────────────────────────────────────────────────
    inventory = [
        ("Rice",        "kg", 40, 10),
        ("Chicken",     "kg", 25, 8),
        ("Paneer",      "kg", 12, 5),
        ("Vegetables",  "kg", 30, 10),
        ("Cooking Oil", "l",  18, 5),
    ]
    c.executemany(
        "INSERT INTO inventory(item_name, unit, quantity, low_stock_at) VALUES (?,?,?,?)",
        inventory
    )
    print(f"  ✓ {len(inventory)} inventory items")

    # ── Sample admin notification ────────────────────────────────────────────
    c.execute(
        "INSERT INTO notifications(user_id, audience, title, message, type) VALUES (NULL,'admin',?,?,?)",
        ("Welcome to SmartFood Admin", "Your upgraded dashboard with live monitoring is ready.", "info")
    )

    conn.commit()
    conn.close()
    print("✅ Database seeded!\n")
