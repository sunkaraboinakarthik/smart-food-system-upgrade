"""Cart routes — /api/cart/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required
from utils.activity import log_activity

cart_bp = Blueprint("cart", __name__, url_prefix="/api/cart")


def build_cart_response(db, user_id):
    rows = db.execute("""
        SELECT c.id, c.food_item_id, c.quantity,
               f.name, f.price, f.img, f.emoji, f.type,
               r.id as restaurant_id, r.name as restaurant_name
        FROM cart c
        JOIN food_items f ON c.food_item_id = f.id
        JOIN restaurants r ON f.restaurant_id = r.id
        WHERE c.user_id=? AND c.saved_for_later=0
    """, (user_id,)).fetchall()

    items = [dict(r) for r in rows]
    subtotal    = sum(i["price"] * i["quantity"] for i in items)
    delivery_fee = 0 if subtotal >= 500 else 40
    return {
        "items":        items,
        "subtotal":     round(subtotal, 2),
        "delivery_fee": delivery_fee,
        "total":        round(subtotal + delivery_fee, 2),
        "item_count":   sum(i["quantity"] for i in items),
    }


@cart_bp.get("")
@token_required
def get_cart():
    db   = get_db()
    data = build_cart_response(db, request.current_user["sub"])
    db.close()
    return jsonify({"success": True, "data": data})


@cart_bp.post("")
@token_required
def add_to_cart():
    body         = request.get_json(silent=True) or {}
    food_item_id = body.get("food_item_id")
    quantity     = int(body.get("quantity", 1))

    if not food_item_id:
        return jsonify({"success": False, "message": "food_item_id required"}), 400

    db   = get_db()
    food = db.execute("SELECT * FROM food_items WHERE id=? AND is_available=1", (food_item_id,)).fetchone()
    if not food:
        db.close()
        return jsonify({"success": False, "message": "Food item not found or unavailable"}), 404

    user_id = request.current_user["sub"]

    # Restaurant conflict check
    existing = db.execute("""
        SELECT f.restaurant_id FROM cart c
        JOIN food_items f ON c.food_item_id = f.id
        WHERE c.user_id=? LIMIT 1
    """, (user_id,)).fetchone()

    if existing and existing["restaurant_id"] != food["restaurant_id"]:
        db.close()
        return jsonify({
            "success": False,
            "message": "Your cart has items from another restaurant. Clear cart to add this item.",
            "conflict": True
        }), 409

    # Upsert
    existing_row = db.execute("SELECT id, quantity FROM cart WHERE user_id=? AND food_item_id=?", (user_id, food_item_id)).fetchone()
    if existing_row:
        db.execute("UPDATE cart SET quantity=? WHERE id=?", (existing_row["quantity"] + quantity, existing_row["id"]))
    else:
        db.execute("INSERT INTO cart(user_id, food_item_id, quantity) VALUES(?,?,?)", (user_id, food_item_id, quantity))
    db.commit()

    cart = build_cart_response(db, user_id)
    db.close()
    log_activity(user_id, request.current_user["name"], "cart_add", f"Added {food['name']} x{quantity}")
    return jsonify({"success": True, "message": "Added to cart", "data": cart}), 201


@cart_bp.put("/<int:item_id>")
@token_required
def update_cart_item(item_id):
    body     = request.get_json(silent=True) or {}
    quantity = body.get("quantity")
    if quantity is None:
        return jsonify({"success": False, "message": "quantity required"}), 400

    user_id = request.current_user["sub"]
    db      = get_db()
    row     = db.execute("SELECT * FROM cart WHERE id=? AND user_id=?", (item_id, user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({"success": False, "message": "Cart item not found"}), 404

    if int(quantity) <= 0:
        db.execute("DELETE FROM cart WHERE id=?", (item_id,))
    else:
        db.execute("UPDATE cart SET quantity=? WHERE id=?", (int(quantity), item_id))
    db.commit()
    cart = build_cart_response(db, user_id)
    db.close()
    return jsonify({"success": True, "message": "Cart updated", "data": cart})


@cart_bp.delete("/<int:item_id>")
@token_required
def remove_from_cart(item_id):
    user_id = request.current_user["sub"]
    db      = get_db()
    row     = db.execute("SELECT id FROM cart WHERE id=? AND user_id=?", (item_id, user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({"success": False, "message": "Cart item not found"}), 404
    db.execute("DELETE FROM cart WHERE id=?", (item_id,))
    db.commit()
    cart = build_cart_response(db, user_id)
    db.close()
    log_activity(user_id, request.current_user["name"], "cart_remove", f"Removed cart item #{item_id}")
    return jsonify({"success": True, "message": "Item removed", "data": cart})


@cart_bp.delete("")
@token_required
def clear_cart():
    db = get_db()
    db.execute("DELETE FROM cart WHERE user_id=?", (request.current_user["sub"],))
    db.commit()
    db.close()
    log_activity(request.current_user["sub"], request.current_user["name"], "cart_clear", "Cleared entire cart")
    return jsonify({"success": True, "message": "Cart cleared"})


@cart_bp.post("/<int:item_id>/save-for-later")
@token_required
def save_for_later(item_id):
    db = get_db()
    row = db.execute("SELECT id FROM cart WHERE id=? AND user_id=?", (item_id, request.current_user["sub"])).fetchone()
    if not row:
        db.close()
        return jsonify({"success": False, "message": "Cart item not found"}), 404
    db.execute("UPDATE cart SET saved_for_later=1 WHERE id=?", (item_id,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Saved for later"})


@cart_bp.post("/<int:item_id>/move-to-cart")
@token_required
def move_saved_to_cart(item_id):
    db = get_db()
    row = db.execute("SELECT id FROM cart WHERE id=? AND user_id=?", (item_id, request.current_user["sub"])).fetchone()
    if not row:
        db.close()
        return jsonify({"success": False, "message": "Cart item not found"}), 404
    db.execute("UPDATE cart SET saved_for_later=0 WHERE id=?", (item_id,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Moved back to cart"})


@cart_bp.get("/saved")
@token_required
def get_saved_items():
    db = get_db()
    rows = db.execute("""
        SELECT c.id, c.food_item_id, c.quantity, f.name, f.price, f.img, f.emoji
        FROM cart c JOIN food_items f ON c.food_item_id = f.id
        WHERE c.user_id=? AND c.saved_for_later=1
    """, (request.current_user["sub"],)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@cart_bp.post("/promo")
@token_required
def validate_promo():
    body     = request.get_json(silent=True) or {}
    code     = (body.get("code") or "").strip().upper()
    subtotal = float(body.get("subtotal", 0))
    if not code:
        return jsonify({"success": False, "message": "code required"}), 400

    db    = get_db()
    promo = db.execute("SELECT * FROM promo_codes WHERE code=? AND is_active=1", (code,)).fetchone()
    db.close()

    if not promo:
        return jsonify({"success": False, "message": "Invalid or expired promo code"}), 400
    if subtotal < promo["min_order"]:
        return jsonify({"success": False, "message": f"Minimum order ₹{int(promo['min_order'])} required for this code"}), 400

    discount = promo["value"] if promo["type"] == "flat" else round(subtotal * promo["value"] / 100, 2)
    return jsonify({"success": True, "message": "Promo code applied!", "data": {
        "code":        promo["code"],
        "discount":    discount,
        "description": promo["description"],
    }})
