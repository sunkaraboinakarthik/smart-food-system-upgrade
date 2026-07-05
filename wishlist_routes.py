"""Wishlist routes — /api/wishlist/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required
from utils.activity import log_activity

wishlist_bp = Blueprint("wishlist", __name__, url_prefix="/api/wishlist")


@wishlist_bp.get("")
@token_required
def list_wishlist():
    db = get_db()
    rows = db.execute("""
        SELECT w.id, f.* FROM wishlist w
        JOIN food_items f ON w.food_item_id = f.id
        WHERE w.user_id=?
        ORDER BY w.id DESC
    """, (request.current_user["sub"],)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@wishlist_bp.post("")
@token_required
def add_wishlist():
    body = request.get_json(silent=True) or {}
    food_item_id = body.get("food_item_id")
    if not food_item_id:
        return jsonify({"success": False, "message": "food_item_id required"}), 400
    db = get_db()
    try:
        db.execute("INSERT OR IGNORE INTO wishlist(user_id, food_item_id) VALUES (?,?)",
                   (request.current_user["sub"], food_item_id))
        db.commit()
    finally:
        db.close()
    return jsonify({"success": True, "message": "Added to wishlist"}), 201


@wishlist_bp.delete("/<int:food_item_id>")
@token_required
def remove_wishlist(food_item_id):
    db = get_db()
    db.execute("DELETE FROM wishlist WHERE user_id=? AND food_item_id=?",
               (request.current_user["sub"], food_item_id))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Removed from wishlist"})


@wishlist_bp.post("/<int:food_item_id>/move-to-cart")
@token_required
def move_to_cart(food_item_id):
    user_id = request.current_user["sub"]
    db = get_db()
    food = db.execute("SELECT * FROM food_items WHERE id=? AND is_available=1", (food_item_id,)).fetchone()
    if not food:
        db.close()
        return jsonify({"success": False, "message": "Food item not available"}), 404
    existing = db.execute("SELECT id, quantity FROM cart WHERE user_id=? AND food_item_id=?",
                           (user_id, food_item_id)).fetchone()
    if existing:
        db.execute("UPDATE cart SET quantity=quantity+1 WHERE id=?", (existing["id"],))
    else:
        db.execute("INSERT INTO cart(user_id, food_item_id, quantity) VALUES (?,?,1)", (user_id, food_item_id))
    db.execute("DELETE FROM wishlist WHERE user_id=? AND food_item_id=?", (user_id, food_item_id))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Moved to cart"})
