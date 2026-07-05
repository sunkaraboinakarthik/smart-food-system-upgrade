"""Admin routes — /api/admin/*"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from database import get_db
from auth_utils import token_required, role_required, hash_password
from utils.activity import log_activity, push_notification

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ── Dashboard stats (all cards required by the spec) ───────────────────────────
@admin_bp.get("/stats")
@role_required("admin")
def stats():
    db = get_db()
    orders = [dict(o) for o in db.execute("SELECT * FROM orders").fetchall()]
    today  = datetime.now().strftime("%Y-%m-%d")
    month  = datetime.now().strftime("%Y-%m")

    by_status = {}
    for o in orders:
        by_status[o["status"]] = by_status.get(o["status"], 0) + 1

    today_orders   = [o for o in orders if o["created_at"].startswith(today)]
    month_orders   = [o for o in orders if o["created_at"].startswith(month)]

    revenue_chart = []
    for i in range(6, -1, -1):
        d   = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        lbl = (datetime.now() - timedelta(days=i)).strftime("%a %d")
        rev = sum(o["total"] for o in orders if o["created_at"].startswith(d) and o["status"] == "Delivered")
        revenue_chart.append({"date": lbl, "revenue": round(rev, 2)})

    rest_counts = {}
    for o in orders:
        nm = o.get("restaurant_name", "Unknown")
        rest_counts[nm] = rest_counts.get(nm, 0) + 1

    total_users   = db.execute("SELECT COUNT(*) c FROM users WHERE role='user'").fetchone()["c"]
    online_users  = db.execute("SELECT COUNT(*) c FROM users WHERE is_online=1").fetchone()["c"]
    today_regs    = db.execute("SELECT COUNT(*) c FROM users WHERE created_at LIKE ?", (f"{today}%",)).fetchone()["c"]

    # best/least selling food + top customers
    best_selling = db.execute("""
        SELECT name, SUM(quantity) qty FROM order_items GROUP BY name ORDER BY qty DESC LIMIT 5
    """).fetchall()
    least_selling = db.execute("""
        SELECT name, SUM(quantity) qty FROM order_items GROUP BY name ORDER BY qty ASC LIMIT 5
    """).fetchall()
    top_customers = db.execute("""
        SELECT user_name, COUNT(*) orders_count, SUM(total) total_spent
        FROM orders WHERE status='Delivered' GROUP BY user_id ORDER BY total_spent DESC LIMIT 5
    """).fetchall()

    recent_activity = db.execute("""
        SELECT * FROM activity_logs ORDER BY id DESC LIMIT 30
    """).fetchall()

    low_stock = db.execute("SELECT * FROM inventory WHERE quantity <= low_stock_at").fetchall()

    db.close()
    return jsonify({"success": True, "data": {
        "total_users":          total_users,
        "online_users":         online_users,
        "today_registrations":  today_regs,
        "total_orders":         len(orders),
        "pending_orders":       by_status.get("Pending", 0),
        "preparing_orders":     by_status.get("Preparing", 0),
        "out_for_delivery_orders": by_status.get("On The Way", 0) + by_status.get("Out for Delivery", 0),
        "delivered_orders":     by_status.get("Delivered", 0),
        "cancelled_orders":     by_status.get("Cancelled", 0),
        "today_revenue":        round(sum(o["total"] for o in today_orders if o["status"] == "Delivered"), 2),
        "monthly_revenue":      round(sum(o["total"] for o in month_orders if o["status"] == "Delivered"), 2),
        "total_revenue":        round(sum(o["total"] for o in orders if o["status"] == "Delivered"), 2),
        "by_status":            by_status,
        "revenue_chart":        revenue_chart,
        "top_restaurants":      sorted([{"name": k, "orders": v} for k, v in rest_counts.items()], key=lambda x: -x["orders"])[:5],
        "best_selling_food":    [dict(r) for r in best_selling],
        "least_selling_food":   [dict(r) for r in least_selling],
        "top_customers":        [dict(r) for r in top_customers],
        "recent_activity":      [dict(r) for r in recent_activity],
        "low_stock_alerts":     [dict(r) for r in low_stock],
    }})


# ── Users ─────────────────────────────────────────────────────────────────────
@admin_bp.get("/users")
@role_required("admin")
def list_users():
    q = request.args.get("q", "").strip()
    db = get_db()
    if q:
        like = f"%{q}%"
        users = db.execute("""
            SELECT id,name,username,email,role,phone,country_code,address,is_active,is_blocked,
                   is_online,email_verified,created_at
            FROM users WHERE name LIKE ? OR email LIKE ? OR phone LIKE ?
        """, (like, like, like)).fetchall()
    else:
        users = db.execute("""
            SELECT id,name,username,email,role,phone,country_code,address,is_active,is_blocked,
                   is_online,email_verified,created_at
            FROM users
        """).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(u) for u in users]})


@admin_bp.put("/users/<int:uid>")
@role_required("admin")
def update_user(uid):
    data    = request.get_json(silent=True) or {}
    allowed = ("name", "role", "address", "phone", "is_active")
    sets    = [f"{k}=?" for k in data if k in allowed]
    vals    = [data[k] for k in data if k in allowed]
    if not sets:
        return jsonify({"success": False, "message": "Nothing to update"}), 400
    db = get_db()
    db.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", vals + [uid])
    db.commit()
    user = db.execute("SELECT id,name,email,role,phone,address,is_active FROM users WHERE id=?", (uid,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "User updated", "data": dict(user)})


@admin_bp.patch("/users/<int:uid>/block")
@role_required("admin")
def block_user(uid):
    db = get_db()
    db.execute("UPDATE users SET is_blocked=1 WHERE id=?", (uid,))
    db.commit()
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "admin_block_user", f"Blocked user #{uid}")
    return jsonify({"success": True, "message": "User blocked"})


@admin_bp.patch("/users/<int:uid>/unblock")
@role_required("admin")
def unblock_user(uid):
    db = get_db()
    db.execute("UPDATE users SET is_blocked=0 WHERE id=?", (uid,))
    db.commit()
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "admin_unblock_user", f"Unblocked user #{uid}")
    return jsonify({"success": True, "message": "User unblocked"})


@admin_bp.delete("/users/<int:uid>")
@role_required("admin")
def delete_user(uid):
    db = get_db()
    db.execute("DELETE FROM users WHERE id=?", (uid,))
    db.commit()
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "admin_delete_user", f"Deleted user #{uid}")
    return jsonify({"success": True, "message": "User deleted"})


@admin_bp.post("/users/<int:uid>/reset-password")
@role_required("admin")
def admin_reset_password(uid):
    data = request.get_json(silent=True) or {}
    new_password = data.get("newPassword") or "SmartFood@123"
    db = get_db()
    db.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_password), uid))
    db.commit()
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "admin_reset_password", f"Reset password for user #{uid}")
    return jsonify({"success": True, "message": "Password reset. Share the temporary password with the user securely.",
                     "data": {"temporary_password": new_password}})


@admin_bp.get("/users/<int:uid>/login-history")
@role_required("admin")
def user_login_history(uid):
    db = get_db()
    rows = db.execute("SELECT * FROM login_history WHERE user_id=? ORDER BY id DESC LIMIT 50", (uid,)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@admin_bp.get("/users/<int:uid>/orders")
@role_required("admin")
def user_orders(uid):
    db = get_db()
    rows = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (uid,)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


# ── Activity / audit logs ──────────────────────────────────────────────────────
@admin_bp.get("/activity-logs")
@role_required("admin")
def activity_logs():
    limit = min(int(request.args.get("limit", 100)), 500)
    db = get_db()
    rows = db.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@admin_bp.get("/online-users")
@role_required("admin")
def online_users():
    db = get_db()
    rows = db.execute("SELECT id, name, email, last_seen FROM users WHERE is_online=1").fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


# ── Delivery agents ───────────────────────────────────────────────────────────
@admin_bp.get("/agents")
@token_required
def list_agents():
    db     = get_db()
    agents = [dict(a) for a in db.execute("SELECT * FROM delivery_agents").fetchall()]
    orders = [dict(o) for o in db.execute("SELECT agent_id, status FROM orders WHERE agent_id!=''").fetchall()]
    for a in agents:
        a["active_orders"]    = sum(1 for o in orders if o["agent_id"] == a["agent_code"] and o["status"] not in ("Delivered", "Cancelled"))
        a["completed_orders"] = sum(1 for o in orders if o["agent_id"] == a["agent_code"] and o["status"] == "Delivered")
    db.close()
    return jsonify({"success": True, "data": agents})


@admin_bp.post("/agents")
@role_required("admin")
def create_agent():
    data = request.get_json(silent=True) or {}
    if not data.get("agent_code") or not data.get("name"):
        return jsonify({"success": False, "message": "agent_code and name required"}), 400
    db = get_db()
    db.execute("INSERT INTO delivery_agents(agent_code,name,phone) VALUES(?,?,?)",
               (data["agent_code"], data["name"], data.get("phone", "")))
    db.commit()
    agent = db.execute("SELECT * FROM delivery_agents ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    return jsonify({"success": True, "message": "Agent created", "data": dict(agent)}), 201


@admin_bp.put("/agents/<int:aid>")
@role_required("admin")
def update_agent(aid):
    data    = request.get_json(silent=True) or {}
    allowed = ("name", "phone", "rating", "is_available")
    sets    = [f"{k}=?" for k in data if k in allowed]
    vals    = [data[k] for k in data if k in allowed]
    if not sets:
        return jsonify({"success": False, "message": "Nothing to update"}), 400
    db = get_db()
    db.execute(f"UPDATE delivery_agents SET {', '.join(sets)} WHERE id=?", vals + [aid])
    db.commit()
    agent = db.execute("SELECT * FROM delivery_agents WHERE id=?", (aid,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "Agent updated", "data": dict(agent)})


# ── Promo codes (legacy alias — prefer /api/coupons) ───────────────────────────
@admin_bp.get("/promos")
@role_required("admin")
def list_promos():
    db     = get_db()
    promos = db.execute("SELECT * FROM promo_codes").fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(p) for p in promos]})
