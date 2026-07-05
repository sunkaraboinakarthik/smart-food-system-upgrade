"""Search and reviews — /api/search, /api/promos, /api/restaurants/:id/reviews"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required

misc_bp = Blueprint("misc", __name__, url_prefix="/api")


@misc_bp.get("/search")
def search():
    q = (request.args.get("q") or "").strip().lower()
    if len(q) < 2:
        return jsonify({"success": False, "message": "Query must be at least 2 characters"}), 400

    db = get_db()
    restaurants = [dict(r) for r in db.execute("SELECT * FROM restaurants").fetchall()
                   if q in r["name"].lower() or q in r["cuisine"].lower()]
    food = [dict(f) for f in db.execute("SELECT * FROM food_items WHERE is_available=1").fetchall()
            if q in f["name"].lower() or q in (f["description"] or "").lower()][:10]
    db.close()

    return jsonify({"success": True, "data": {
        "restaurants": restaurants,
        "food":        food,
        "total":       len(restaurants) + len(food)
    }})


@misc_bp.get("/promos")
def public_promos():
    db     = get_db()
    promos = db.execute(
        "SELECT code,type,value,min_order,description,expires_at FROM promo_codes WHERE is_active=1"
    ).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(p) for p in promos]})


@misc_bp.get("/restaurants/<int:rid>/reviews")
def get_reviews(rid):
    db = get_db()
    r  = db.execute("SELECT id FROM restaurants WHERE id=?", (rid,)).fetchone()
    if not r:
        db.close()
        return jsonify({"success": False, "message": "Restaurant not found"}), 404
    reviews = db.execute("SELECT * FROM reviews WHERE restaurant_id=? ORDER BY id DESC", (rid,)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(rv) for rv in reviews]})


@misc_bp.post("/restaurants/<int:rid>/reviews")
@token_required
def post_review(rid):
    body    = request.get_json(silent=True) or {}
    rating  = body.get("rating")
    comment = body.get("comment", "")

    if not rating:
        return jsonify({"success": False, "message": "rating required"}), 400
    rating = float(rating)
    if not (1 <= rating <= 5):
        return jsonify({"success": False, "message": "rating must be between 1 and 5"}), 400

    db = get_db()
    r  = db.execute("SELECT id FROM restaurants WHERE id=?", (rid,)).fetchone()
    if not r:
        db.close()
        return jsonify({"success": False, "message": "Restaurant not found"}), 404

    db.execute(
        "INSERT INTO reviews(restaurant_id,user_id,user_name,rating,comment) VALUES(?,?,?,?,?)",
        (rid, request.current_user["sub"], request.current_user["name"], rating, comment)
    )

    # Recompute avg rating
    avg = db.execute("SELECT AVG(rating) as a FROM reviews WHERE restaurant_id=?", (rid,)).fetchone()["a"]
    db.execute("UPDATE restaurants SET rating=? WHERE id=?", (round(avg, 1), rid))
    db.commit()

    review = db.execute("SELECT * FROM reviews ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    return jsonify({"success": True, "message": "Review submitted", "data": dict(review)}), 201
