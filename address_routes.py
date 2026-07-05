"""Saved addresses — /api/addresses/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required

address_bp = Blueprint("addresses", __name__, url_prefix="/api/addresses")


@address_bp.get("")
@token_required
def list_addresses():
    db = get_db()
    rows = db.execute("SELECT * FROM addresses WHERE user_id=? ORDER BY is_default DESC, id DESC",
                       (request.current_user["sub"],)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@address_bp.post("")
@token_required
def add_address():
    b = request.get_json(silent=True) or {}
    line1 = (b.get("line1") or "").strip()
    if not line1:
        return jsonify({"success": False, "message": "line1 is required"}), 400
    user_id = request.current_user["sub"]
    db = get_db()
    if b.get("is_default"):
        db.execute("UPDATE addresses SET is_default=0 WHERE user_id=?", (user_id,))
    db.execute("""
        INSERT INTO addresses(user_id, label, line1, line2, city, state, pincode, is_default)
        VALUES (?,?,?,?,?,?,?,?)
    """, (user_id, b.get("label", "Home"), line1, b.get("line2", ""), b.get("city", ""),
          b.get("state", ""), b.get("pincode", ""), 1 if b.get("is_default") else 0))
    db.commit()
    row = db.execute("SELECT * FROM addresses ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    return jsonify({"success": True, "message": "Address added", "data": dict(row)}), 201


@address_bp.put("/<int:addr_id>")
@token_required
def update_address(addr_id):
    b = request.get_json(silent=True) or {}
    user_id = request.current_user["sub"]
    db = get_db()
    row = db.execute("SELECT * FROM addresses WHERE id=? AND user_id=?", (addr_id, user_id)).fetchone()
    if not row:
        db.close()
        return jsonify({"success": False, "message": "Address not found"}), 404
    if b.get("is_default"):
        db.execute("UPDATE addresses SET is_default=0 WHERE user_id=?", (user_id,))
    fields = ["label", "line1", "line2", "city", "state", "pincode"]
    updates = [f"{f}=?" for f in fields if f in b]
    params = [b[f] for f in fields if f in b]
    if "is_default" in b:
        updates.append("is_default=?")
        params.append(1 if b["is_default"] else 0)
    if updates:
        params.append(addr_id)
        db.execute(f"UPDATE addresses SET {', '.join(updates)} WHERE id=?", params)
        db.commit()
    row = db.execute("SELECT * FROM addresses WHERE id=?", (addr_id,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "Address updated", "data": dict(row)})


@address_bp.delete("/<int:addr_id>")
@token_required
def delete_address(addr_id):
    db = get_db()
    db.execute("DELETE FROM addresses WHERE id=? AND user_id=?", (addr_id, request.current_user["sub"]))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Address deleted"})
