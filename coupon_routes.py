"""Coupon management (admin) — /api/coupons/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required, role_required
from utils.activity import log_activity

coupon_bp = Blueprint("coupons", __name__, url_prefix="/api/coupons")


@coupon_bp.get("")
@token_required
def list_coupons():
    db = get_db()
    rows = db.execute("SELECT * FROM promo_codes ORDER BY id DESC").fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@coupon_bp.post("")
@role_required("admin")
def create_coupon():
    b = request.get_json(silent=True) or {}
    code = (b.get("code") or "").strip().upper()
    ctype = b.get("type")
    value = b.get("value")
    if not code or ctype not in ("flat", "percent") or value is None:
        return jsonify({"success": False, "message": "code, type ('flat'|'percent'), and value are required"}), 400

    db = get_db()
    if db.execute("SELECT id FROM promo_codes WHERE code=?", (code,)).fetchone():
        db.close()
        return jsonify({"success": False, "message": "Coupon code already exists"}), 400
    db.execute("""
        INSERT INTO promo_codes(code, type, value, min_order, description, is_active, expires_at, usage_limit)
        VALUES (?,?,?,?,?,?,?,?)
    """, (code, ctype, value, b.get("min_order", 0), b.get("description", ""),
          1 if b.get("is_active", True) else 0, b.get("expires_at", ""), b.get("usage_limit", 0)))
    db.commit()
    row = db.execute("SELECT * FROM promo_codes WHERE code=?", (code,)).fetchone()
    db.close()
    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "admin_coupon_create", f"Created coupon {code}")
    return jsonify({"success": True, "message": "Coupon created", "data": dict(row)}), 201


@coupon_bp.put("/<int:cid>")
@role_required("admin")
def update_coupon(cid):
    b = request.get_json(silent=True) or {}
    fields = ["type", "value", "min_order", "description", "expires_at", "usage_limit"]
    updates = [f"{f}=?" for f in fields if f in b]
    params = [b[f] for f in fields if f in b]
    if "is_active" in b:
        updates.append("is_active=?")
        params.append(1 if b["is_active"] else 0)
    if not updates:
        return jsonify({"success": False, "message": "Nothing to update"}), 400
    params.append(cid)
    db = get_db()
    db.execute(f"UPDATE promo_codes SET {', '.join(updates)} WHERE id=?", params)
    db.commit()
    row = db.execute("SELECT * FROM promo_codes WHERE id=?", (cid,)).fetchone()
    db.close()
    if not row:
        return jsonify({"success": False, "message": "Coupon not found"}), 404
    return jsonify({"success": True, "message": "Coupon updated", "data": dict(row)})


@coupon_bp.delete("/<int:cid>")
@role_required("admin")
def delete_coupon(cid):
    db = get_db()
    db.execute("DELETE FROM promo_codes WHERE id=?", (cid,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Coupon deleted"})
