"""Restaurant & food item routes — /api/restaurants/* and /api/food/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required, role_required

restaurant_bp = Blueprint("restaurants", __name__, url_prefix="/api")


def r_dict(row):
    return dict(row)


# ── Restaurants ───────────────────────────────────────────────────────────────

@restaurant_bp.get("/restaurants")
def list_restaurants():
    db   = get_db()
    rows = db.execute("SELECT * FROM restaurants").fetchall()
    restaurants = [dict(r) for r in rows]

    q       = request.args.get("q", "").lower()
    cuisine = request.args.get("cuisine", "").lower()
    open_   = request.args.get("open")
    sort    = request.args.get("sort")

    if q:
        restaurants = [r for r in restaurants if q in r["name"].lower() or q in r["cuisine"].lower()]
    if cuisine:
        restaurants = [r for r in restaurants if cuisine in r["cuisine"].lower()]
    if open_ == "true":
        restaurants = [r for r in restaurants if r["is_open"]]
    if sort == "rating":
        restaurants.sort(key=lambda r: r["rating"], reverse=True)
    elif sort == "delivery":
        restaurants.sort(key=lambda r: int(r["delivery_time"].split("-")[0]))

    db.close()
    return jsonify({"success": True, "data": restaurants})


@restaurant_bp.get("/restaurants/<int:rid>")
def get_restaurant(rid):
    db = get_db()
    r  = db.execute("SELECT * FROM restaurants WHERE id=?", (rid,)).fetchone()
    db.close()
    if not r:
        return jsonify({"success": False, "message": "Restaurant not found"}), 404
    return jsonify({"success": True, "data": dict(r)})


@restaurant_bp.post("/restaurants")
@role_required("admin")
def create_restaurant():
    data = request.get_json(silent=True) or {}
    if not data.get("name") or not data.get("cuisine"):
        return jsonify({"success": False, "message": "name and cuisine required"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO restaurants(name,cuisine,delivery_time,min_order,img,emoji,discount) VALUES(?,?,?,?,?,?,?)",
        (data["name"], data["cuisine"], data.get("delivery_time","30-40 min"),
         data.get("min_order",200), data.get("img",""), data.get("emoji","🍽️"), data.get("discount",""))
    )
    db.commit()
    r = db.execute("SELECT * FROM restaurants ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    return jsonify({"success": True, "message": "Restaurant created", "data": dict(r)}), 201


@restaurant_bp.put("/restaurants/<int:rid>")
@role_required("admin")
def update_restaurant(rid):
    db = get_db()
    r  = db.execute("SELECT id FROM restaurants WHERE id=?", (rid,)).fetchone()
    if not r:
        db.close()
        return jsonify({"success": False, "message": "Not found"}), 404
    data    = request.get_json(silent=True) or {}
    allowed = ("name","cuisine","rating","delivery_time","min_order","img","emoji","discount","is_open")
    sets    = [f"{k}=?" for k in data if k in allowed]
    vals    = [data[k] for k in data if k in allowed]
    if sets:
        db.execute(f"UPDATE restaurants SET {', '.join(sets)} WHERE id=?", vals + [rid])
        db.commit()
    r = db.execute("SELECT * FROM restaurants WHERE id=?", (rid,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "Updated", "data": dict(r)})


@restaurant_bp.delete("/restaurants/<int:rid>")
@role_required("admin")
def delete_restaurant(rid):
    db = get_db()
    db.execute("DELETE FROM restaurants WHERE id=?", (rid,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Restaurant deleted"})


# ── Restaurant Menu ───────────────────────────────────────────────────────────

@restaurant_bp.get("/restaurants/<int:rid>/menu")
def get_menu(rid):
    db = get_db()
    r  = db.execute("SELECT * FROM restaurants WHERE id=?", (rid,)).fetchone()
    if not r:
        db.close()
        return jsonify({"success": False, "message": "Restaurant not found"}), 404

    query  = "SELECT * FROM food_items WHERE restaurant_id=? AND is_available=1"
    params = [rid]

    if request.args.get("type"):
        query += " AND type=?";  params.append(request.args["type"])
    if request.args.get("category"):
        query += " AND category=?"; params.append(request.args["category"])
    if request.args.get("popular") == "true":
        query += " AND is_popular=1"

    items = [dict(i) for i in db.execute(query, params).fetchall()]

    # Group by category
    categories = sorted(set(i["category"] for i in items))
    db.close()
    return jsonify({"success": True, "data": {"restaurant": dict(r), "items": items, "categories": categories}})


# ── Food Items ────────────────────────────────────────────────────────────────

@restaurant_bp.get("/food/popular")
def popular_food():
    db    = get_db()
    items = db.execute("SELECT * FROM food_items WHERE is_popular=1 AND is_available=1 LIMIT 12").fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(i) for i in items]})


@restaurant_bp.get("/food/<int:fid>")
def get_food(fid):
    db = get_db()
    item = db.execute("SELECT * FROM food_items WHERE id=?", (fid,)).fetchone()
    db.close()
    if not item:
        return jsonify({"success": False, "message": "Food item not found"}), 404
    return jsonify({"success": True, "data": dict(item)})


@restaurant_bp.post("/food")
@role_required("admin")
def create_food():
    data = request.get_json(silent=True) or {}
    if not data.get("restaurant_id") or not data.get("name") or not data.get("price"):
        return jsonify({"success": False, "message": "restaurant_id, name, price required"}), 400
    db = get_db()
    r  = db.execute("SELECT id FROM restaurants WHERE id=?", (data["restaurant_id"],)).fetchone()
    if not r:
        db.close()
        return jsonify({"success": False, "message": "Restaurant not found"}), 404
    db.execute(
        "INSERT INTO food_items(restaurant_id,name,price,description,img,emoji,type,category,is_popular) VALUES(?,?,?,?,?,?,?,?,?)",
        (data["restaurant_id"], data["name"], float(data["price"]),
         data.get("description",""), data.get("img",""), data.get("emoji","🍽️"),
         data.get("type","veg"), data.get("category","Main"), int(data.get("is_popular",0)))
    )
    db.commit()
    item = db.execute("SELECT * FROM food_items ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    return jsonify({"success": True, "message": "Food item created", "data": dict(item)}), 201


@restaurant_bp.put("/food/<int:fid>")
@role_required("admin")
def update_food(fid):
    db   = get_db()
    item = db.execute("SELECT id FROM food_items WHERE id=?", (fid,)).fetchone()
    if not item:
        db.close()
        return jsonify({"success": False, "message": "Not found"}), 404
    data    = request.get_json(silent=True) or {}
    allowed = ("name","price","description","img","emoji","type","category","is_popular","is_available","rating")
    sets    = [f"{k}=?" for k in data if k in allowed]
    vals    = [data[k] for k in data if k in allowed]
    if sets:
        db.execute(f"UPDATE food_items SET {', '.join(sets)} WHERE id=?", vals + [fid])
        db.commit()
    item = db.execute("SELECT * FROM food_items WHERE id=?", (fid,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "Updated", "data": dict(item)})


@restaurant_bp.delete("/food/<int:fid>")
@role_required("admin")
def delete_food(fid):
    db = get_db()
    db.execute("DELETE FROM food_items WHERE id=?", (fid,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Food item deleted"})
