"""
SmartFood Backend — Flask + SQLite + Flask-SocketIO
Run: python app.py  (default port 5000)
     PORT=8000 python app.py
"""
import os
from flask import Flask, jsonify, send_from_directory

# ── App setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "smartfood_secret_2024")
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB upload cap (profile pictures)

UPLOAD_ROOT = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(os.path.join(UPLOAD_ROOT, "profile_pics"), exist_ok=True)


# ── CORS (manual, no flask-cors needed) ──────────────────────────────────────
@app.after_request
def add_security_and_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    # Basic security headers (XSS / clickjacking / MIME sniffing hardening)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    return response


@app.before_request
def handle_options():
    from flask import request
    if request.method == "OPTIONS":
        r = app.make_default_options_response()
        r.headers["Access-Control-Allow-Origin"]  = "*"
        r.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        r.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return r


# ── Database init + seeding ───────────────────────────────────────────────────
from database import init_db
from seeder   import seed

init_db()
seed()

# ── Real-time layer (Flask-SocketIO) ──────────────────────────────────────────
from utils.realtime import init_socketio
socketio = init_socketio(app)

# ── Serve uploaded profile pictures ───────────────────────────────────────────
@app.get("/uploads/profile_pics/<path:filename>")
def serve_profile_pic(filename):
    return send_from_directory(os.path.join(UPLOAD_ROOT, "profile_pics"), filename)


# ── Register blueprints ───────────────────────────────────────────────────────
from routes.auth_routes         import auth_bp
from routes.restaurant_routes   import restaurant_bp
from routes.cart_routes         import cart_bp
from routes.order_routes        import order_bp
from routes.admin_routes        import admin_bp
from routes.misc_routes         import misc_bp
from routes.wishlist_routes     import wishlist_bp
from routes.address_routes      import address_bp
from routes.notification_routes import notification_bp
from routes.coupon_routes       import coupon_bp
from routes.inventory_routes    import inventory_bp
from routes.payment_routes      import payment_bp

for bp in (auth_bp, restaurant_bp, cart_bp, order_bp, admin_bp, misc_bp,
           wishlist_bp, address_bp, notification_bp, coupon_bp, inventory_bp, payment_bp):
    app.register_blueprint(bp)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
@app.get("/api")
def index():
    return jsonify({
        "success": True,
        "message": "🍔 SmartFood API is running!",
        "version": "2.0.0",
        "realtime": "enabled" if socketio else "disabled (install flask-socketio)",
        "endpoints": {
            "auth":          ["/api/auth/register", "/api/auth/login", "/api/auth/me",
                               "/api/auth/verify-email-otp", "/api/auth/forgot-password", "/api/auth/reset-password"],
            "restaurants":   ["/api/restaurants", "/api/restaurants/<id>", "/api/restaurants/<id>/menu"],
            "food":          ["/api/food/popular", "/api/food/<id>"],
            "cart":          ["/api/cart", "/api/cart/promo", "/api/cart/saved"],
            "orders":        ["/api/orders", "/api/orders/all", "/api/orders/<id>", "/api/orders/<id>/invoice"],
            "payments":      ["/api/payments/razorpay/create-order", "/api/payments/razorpay/verify", "/api/payments/cod"],
            "wishlist":      ["/api/wishlist"],
            "addresses":     ["/api/addresses"],
            "coupons":       ["/api/coupons"],
            "inventory":     ["/api/inventory"],
            "notifications": ["/api/notifications"],
            "admin":         ["/api/admin/stats", "/api/admin/users", "/api/admin/agents",
                               "/api/admin/activity-logs", "/api/admin/online-users"],
            "misc":          ["/api/search?q=...", "/api/promos", "/api/restaurants/<id>/reviews"],
        }
    })


# ── 404 handler ───────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "message": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "message": "Method not allowed"}), 405

@app.errorhandler(413)
def too_large(e):
    return jsonify({"success": False, "message": "File too large (max 5MB)"}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "message": "Internal server error"}), 500


# ── Start ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"""
╔══════════════════════════════════════════════╗
║   🍔  SmartFood Backend v2 (Flask+SocketIO)  ║
║   Running on http://localhost:{port}            ║
╠══════════════════════════════════════════════╣
║  Auth:     /api/auth/*  (OTP, JWT, roles)    ║
║  Realtime: WebSocket admin live feed          ║
║  Payments: Razorpay + Cash on Delivery        ║
╠══════════════════════════════════════════════╣
║  Demo credentials:                           ║
║  👤 user@smartfood.com     / user123         ║
║  👑 admin@smartfood.com    / admin123        ║
║  🚴 delivery@smartfood.com / delivery123     ║
╚══════════════════════════════════════════════╝
""")
    if socketio:
        socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)
    else:
        app.run(host="0.0.0.0", port=port, debug=False)
