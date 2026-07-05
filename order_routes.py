"""Order routes — /api/orders/*"""
from flask import Blueprint, request, jsonify, Response
from database import get_db
from auth_utils import token_required, role_required
from utils.activity import log_activity, push_notification

order_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

STATUSES = ["Pending", "Preparing", "Picked Up", "On The Way", "Delivered", "Cancelled"]


def fetch_order_with_items(db, order_id):
    order = db.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        return None
    items   = db.execute("SELECT * FROM order_items WHERE order_id=?", (order_id,)).fetchall()
    history = db.execute("SELECT * FROM order_status_history WHERE order_id=? ORDER BY id", (order_id,)).fetchall()
    d = dict(order)
    d["items"]          = [dict(i) for i in items]
    d["status_history"] = [dict(h) for h in history]
    return d


# ── Place order ───────────────────────────────────────────────────────────────
@order_bp.post("")
@token_required
def place_order():
    body            = request.get_json(silent=True) or {}
    payment_method  = body.get("paymentMethod") or body.get("payment_method")
    promo_code      = (body.get("promoCode") or body.get("promo_code") or "").upper()
    delivery_addr   = body.get("deliveryAddress") or body.get("delivery_address") or ""

    if not payment_method:
        return jsonify({"success": False, "message": "paymentMethod required"}), 400

    user_id = request.current_user["sub"]
    db      = get_db()

    # Fetch cart
    cart_rows = db.execute("""
        SELECT c.food_item_id, c.quantity,
               f.name, f.price, f.emoji, f.img, f.restaurant_id
        FROM cart c JOIN food_items f ON c.food_item_id=f.id
        WHERE c.user_id=?
    """, (user_id,)).fetchall()

    if not cart_rows:
        db.close()
        return jsonify({"success": False, "message": "Cart is empty"}), 400

    cart_items = [dict(r) for r in cart_rows]
    subtotal   = sum(i["price"] * i["quantity"] for i in cart_items)
    delivery_fee = 0 if subtotal >= 500 else 40

    # Promo
    discount = 0.0
    applied_promo = ""
    if promo_code:
        promo = db.execute("SELECT * FROM promo_codes WHERE code=? AND is_active=1", (promo_code,)).fetchone()
        if promo and subtotal >= promo["min_order"]:
            discount = promo["value"] if promo["type"] == "flat" else round(subtotal * promo["value"] / 100, 2)
            applied_promo = promo["code"]

    total = max(0, subtotal + delivery_fee - discount)

    rest = db.execute("SELECT id, name FROM restaurants WHERE id=?", (cart_items[0]["restaurant_id"],)).fetchone()
    user = db.execute("SELECT address FROM users WHERE id=?", (user_id,)).fetchone()

    db.execute("""
        INSERT INTO orders(user_id, user_name, user_address, restaurant_id, restaurant_name,
                           payment_method, subtotal, delivery_fee, discount, promo_code, total, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,'Pending')
    """, (user_id, request.current_user["name"],
          delivery_addr or (user["address"] if user else ""),
          rest["id"] if rest else None,
          rest["name"] if rest else "",
          payment_method, round(subtotal,2), delivery_fee, discount, applied_promo, round(total,2)))

    order_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert order items
    for item in cart_items:
        db.execute("""
            INSERT INTO order_items(order_id, food_item_id, name, price, quantity, emoji, img)
            VALUES (?,?,?,?,?,?,?)
        """, (order_id, item["food_item_id"], item["name"], item["price"], item["quantity"], item["emoji"], item["img"]))

    # Status history
    db.execute("INSERT INTO order_status_history(order_id, status) VALUES(?,?)", (order_id, "Pending"))

    # Clear cart
    db.execute("DELETE FROM cart WHERE user_id=?", (user_id,))
    db.commit()

    order = fetch_order_with_items(db, order_id)
    db.close()

    cu = request.current_user
    log_activity(user_id, cu["name"], "order_placed", f"Order #{order_id} placed ({payment_method}) — total ₹{round(total,2)}")
    push_notification(None, "admin", "New Order", f"Order #{order_id} by {cu['name']} — ₹{round(total,2)}", "info")
    push_notification(user_id, "user", "Order Confirmed", f"Your order #{order_id} has been placed", "success")

    return jsonify({"success": True, "message": "Order placed successfully", "data": order}), 201


# ── My orders ─────────────────────────────────────────────────────────────────
@order_bp.get("")
@token_required
def my_orders():
    db     = get_db()
    rows   = db.execute("SELECT id FROM orders WHERE user_id=? ORDER BY id DESC", (request.current_user["sub"],)).fetchall()
    result = [fetch_order_with_items(db, r["id"]) for r in rows]
    db.close()
    return jsonify({"success": True, "data": result})


# ── All orders (admin / delivery) ─────────────────────────────────────────────
@order_bp.get("/all")
@role_required("admin", "delivery")
def all_orders():
    db     = get_db()
    query  = "SELECT id FROM orders"
    params = []

    if request.current_user["role"] == "delivery":
        user = db.execute("SELECT name FROM users WHERE id=?", (request.current_user["sub"],)).fetchone()
        query  = "SELECT id FROM orders WHERE agent_name=?"
        params = [user["name"]] if user else [""]

    status = request.args.get("status")
    if status:
        sep = " AND " if "WHERE" in query else " WHERE "
        query += f"{sep}status=?"
        params.append(status)

    query += " ORDER BY id DESC"
    rows   = db.execute(query, params).fetchall()
    result = [fetch_order_with_items(db, r["id"]) for r in rows]
    db.close()
    return jsonify({"success": True, "data": result})


# ── Single order ──────────────────────────────────────────────────────────────
@order_bp.get("/<int:oid>")
@token_required
def get_order(oid):
    db    = get_db()
    order = fetch_order_with_items(db, oid)
    db.close()
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404
    cu = request.current_user
    if cu["role"] == "user" and order["user_id"] != cu["sub"]:
        return jsonify({"success": False, "message": "Forbidden"}), 403
    return jsonify({"success": True, "data": order})


# ── Update status ─────────────────────────────────────────────────────────────
@order_bp.patch("/<int:oid>/status")
@role_required("admin", "delivery")
def update_status(oid):
    body   = request.get_json(silent=True) or {}
    status = body.get("status")
    note   = body.get("note", "")
    if status not in STATUSES:
        return jsonify({"success": False, "message": f"Invalid status. Must be one of: {', '.join(STATUSES)}"}), 400

    db    = get_db()
    order = db.execute("SELECT id FROM orders WHERE id=?", (oid,)).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404

    db.execute("UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?", (status, oid))
    db.execute("INSERT INTO order_status_history(order_id, status, note) VALUES(?,?,?)", (oid, status, note))
    db.commit()
    order = fetch_order_with_items(db, oid)
    db.close()

    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "order_status_update", f"Order #{oid} -> {status}")
    if order:
        push_notification(order["user_id"], "user", f"Order {status}", f"Your order #{oid} is now {status}", "info")
    if status == "Delivered":
        push_notification(None, "admin", "Delivery Completed", f"Order #{oid} delivered", "success")

    return jsonify({"success": True, "message": f"Status updated to {status}", "data": order})


# ── Assign delivery agent ─────────────────────────────────────────────────────
@order_bp.patch("/<int:oid>/assign")
@role_required("admin")
def assign_agent(oid):
    body       = request.get_json(silent=True) or {}
    agent_code = body.get("agent_code") or body.get("agentCode")
    if not agent_code:
        return jsonify({"success": False, "message": "agent_code required"}), 400

    db    = get_db()
    agent = db.execute("SELECT * FROM delivery_agents WHERE agent_code=?", (agent_code,)).fetchone()
    if not agent:
        db.close()
        return jsonify({"success": False, "message": "Delivery agent not found"}), 404

    order = db.execute("SELECT id FROM orders WHERE id=?", (oid,)).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404

    db.execute("""
        UPDATE orders SET agent_id=?, agent_name=?, agent_phone=?,
                          status='Preparing', updated_at=datetime('now')
        WHERE id=?
    """, (agent["agent_code"], agent["name"], agent["phone"], oid))
    db.execute("INSERT INTO order_status_history(order_id, status, note) VALUES(?,?,?)",
               (oid, "Preparing", f"Assigned to {agent['name']}"))
    db.commit()
    order = fetch_order_with_items(db, oid)
    db.close()
    return jsonify({"success": True, "message": f"Assigned to {agent['name']}", "data": order})


# ── Delivery partner: accept / reject an assigned order ────────────────────────
@order_bp.patch("/<int:oid>/accept")
@role_required("delivery")
def accept_order(oid):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404
    db.execute("UPDATE orders SET status='Picked Up', updated_at=datetime('now') WHERE id=?", (oid,))
    db.execute("INSERT INTO order_status_history(order_id, status, note) VALUES(?,?,?)",
               (oid, "Picked Up", "Accepted by delivery partner"))
    db.commit()
    order = fetch_order_with_items(db, oid)
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "delivery_accept", f"Accepted order #{oid}")
    return jsonify({"success": True, "message": "Order accepted", "data": order})


@order_bp.patch("/<int:oid>/reject")
@role_required("delivery")
def reject_order(oid):
    body = request.get_json(silent=True) or {}
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404
    db.execute("UPDATE orders SET agent_id='', agent_name='', agent_phone='', status='Preparing', "
               "updated_at=datetime('now') WHERE id=?", (oid,))
    db.execute("INSERT INTO order_status_history(order_id, status, note) VALUES(?,?,?)",
               (oid, "Preparing", f"Rejected by delivery partner: {body.get('reason','')}"))
    db.commit()
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "delivery_reject", f"Rejected order #{oid}")
    push_notification(None, "admin", "Delivery Rejected", f"Order #{oid} rejected by {cu['name']} - needs reassignment", "warning")
    return jsonify({"success": True, "message": "Order rejected - sent back for reassignment"})


# ── Cancel order ──────────────────────────────────────────────────────────────
@order_bp.delete("/<int:oid>")
@token_required
def cancel_order(oid):
    db    = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=?", (oid,)).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404

    cu = request.current_user
    if cu["role"] == "user" and order["user_id"] != cu["sub"]:
        db.close()
        return jsonify({"success": False, "message": "Forbidden"}), 403
    if order["status"] in ("Delivered", "Cancelled"):
        db.close()
        return jsonify({"success": False, "message": f"Cannot cancel a {order['status']} order"}), 400

    db.execute("UPDATE orders SET status='Cancelled', updated_at=datetime('now') WHERE id=?", (oid,))
    db.execute("INSERT INTO order_status_history(order_id, status, note) VALUES(?,?,?)",
               (oid, "Cancelled", "Cancelled by user"))
    db.commit()
    db.close()
    log_activity(cu["sub"], cu["name"], "order_cancelled", f"Order #{oid} cancelled")
    push_notification(None, "admin", "Order Cancelled", f"Order #{oid} cancelled by {cu['name']}", "warning")
    return jsonify({"success": True, "message": "Order cancelled"})


# ── Reorder ───────────────────────────────────────────────────────────────────
@order_bp.post("/<int:oid>/reorder")
@token_required
def reorder(oid):
    user_id = request.current_user["sub"]
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (oid, user_id)).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404
    items = db.execute("SELECT * FROM order_items WHERE order_id=?", (oid,)).fetchall()
    added, skipped = 0, 0
    for item in items:
        food = db.execute("SELECT * FROM food_items WHERE id=? AND is_available=1", (item["food_item_id"],)).fetchone()
        if not food:
            skipped += 1
            continue
        existing = db.execute("SELECT id, quantity FROM cart WHERE user_id=? AND food_item_id=?",
                               (user_id, item["food_item_id"])).fetchone()
        if existing:
            db.execute("UPDATE cart SET quantity=quantity+? WHERE id=?", (item["quantity"], existing["id"]))
        else:
            db.execute("INSERT INTO cart(user_id, food_item_id, quantity) VALUES (?,?,?)",
                       (user_id, item["food_item_id"], item["quantity"]))
        added += 1
    db.commit()
    db.close()
    msg = f"{added} item(s) added to cart"
    if skipped:
        msg += f", {skipped} item(s) no longer available"
    return jsonify({"success": True, "message": msg})


# ── Invoice (printable HTML — use browser Print -> Save as PDF) ────────────────
@order_bp.get("/<int:oid>/invoice")
@token_required
def invoice(oid):
    db = get_db()
    order = fetch_order_with_items(db, oid)
    db.close()
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404
    cu = request.current_user
    if cu["role"] == "user" and order["user_id"] != cu["sub"]:
        return jsonify({"success": False, "message": "Forbidden"}), 403

    rows = "".join(
        f"<tr><td>{i['name']}</td><td>{i['quantity']}</td><td>Rs.{i['price']:.2f}</td>"
        f"<td>Rs.{i['price']*i['quantity']:.2f}</td></tr>"
        for i in order["items"]
    )
    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Invoice #{oid}</title>
    <style>
      body{{font-family:Arial,sans-serif;max-width:640px;margin:40px auto;color:#222}}
      h1{{color:#ff5722}} table{{width:100%;border-collapse:collapse;margin-top:16px}}
      th,td{{padding:8px;border-bottom:1px solid #eee;text-align:left}}
      .totals td{{border:none}} .totals tr:last-child td{{font-weight:bold;font-size:1.1em}}
      @media print {{ button{{display:none}} }}
    </style></head><body>
      <h1>SmartFood</h1>
      <p><strong>Invoice</strong> — Order #{oid}<br>Date: {order['created_at']}</p>
      <p>Billed to: {order['user_name']}<br>{order['user_address']}</p>
      <table><thead><tr><th>Item</th><th>Qty</th><th>Price</th><th>Amount</th></tr></thead>
      <tbody>{rows}</tbody></table>
      <table class="totals">
        <tr><td>Subtotal</td><td style="text-align:right">Rs.{order['subtotal']:.2f}</td></tr>
        <tr><td>Delivery Fee</td><td style="text-align:right">Rs.{order['delivery_fee']:.2f}</td></tr>
        <tr><td>Discount</td><td style="text-align:right">-Rs.{order['discount']:.2f}</td></tr>
        <tr><td>Total</td><td style="text-align:right">Rs.{order['total']:.2f}</td></tr>
      </table>
      <p>Payment Method: {order['payment_method']} &nbsp;|&nbsp; Status: {order['status']}</p>
      <button onclick="window.print()">Print / Save as PDF</button>
    </body></html>"""
    return Response(html, mimetype="text/html")
