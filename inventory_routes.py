"""Inventory management (admin) — /api/inventory/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import role_required
from utils.activity import push_notification, log_activity

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


@inventory_bp.get("")
@role_required("admin")
def list_inventory():
    db = get_db()
    rows = db.execute("SELECT * FROM inventory ORDER BY item_name").fetchall()
    db.close()
    data = [dict(r) for r in rows]
    for item in data:
        item["low_stock"] = item["quantity"] <= item["low_stock_at"]
    return jsonify({"success": True, "data": data})


@inventory_bp.post("")
@role_required("admin")
def add_item():
    b = request.get_json(silent=True) or {}
    name = (b.get("item_name") or "").strip()
    if not name:
        return jsonify({"success": False, "message": "item_name required"}), 400
    db = get_db()
    db.execute("""
        INSERT INTO inventory(item_name, unit, quantity, low_stock_at)
        VALUES (?,?,?,?)
        ON CONFLICT(item_name) DO UPDATE SET quantity=excluded.quantity, unit=excluded.unit,
                                              low_stock_at=excluded.low_stock_at, updated_at=datetime('now')
    """, (name, b.get("unit", "kg"), b.get("quantity", 0), b.get("low_stock_at", 5)))
    db.commit()
    row = db.execute("SELECT * FROM inventory WHERE item_name=?", (name,)).fetchone()
    db.close()
    return jsonify({"success": True, "message": "Inventory item saved", "data": dict(row)}), 201


@inventory_bp.patch("/<int:iid>")
@role_required("admin")
def update_item(iid):
    b = request.get_json(silent=True) or {}
    fields = ["unit", "quantity", "low_stock_at"]
    updates = [f"{f}=?" for f in fields if f in b]
    params = [b[f] for f in fields if f in b]
    if not updates:
        return jsonify({"success": False, "message": "Nothing to update"}), 400
    updates.append("updated_at=datetime('now')")
    params.append(iid)
    db = get_db()
    db.execute(f"UPDATE inventory SET {', '.join(updates)} WHERE id=?", params)
    db.commit()
    row = db.execute("SELECT * FROM inventory WHERE id=?", (iid,)).fetchone()
    db.close()
    if not row:
        return jsonify({"success": False, "message": "Item not found"}), 404
    if row["quantity"] <= row["low_stock_at"]:
        push_notification(None, "admin", "Low Stock Alert", f"{row['item_name']} is running low ({row['quantity']} {row['unit']} left)", "warning")
    return jsonify({"success": True, "message": "Inventory updated", "data": dict(row)})


@inventory_bp.delete("/<int:iid>")
@role_required("admin")
def delete_item(iid):
    db = get_db()
    db.execute("DELETE FROM inventory WHERE id=?", (iid,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Item removed"})
