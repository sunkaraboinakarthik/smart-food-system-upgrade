"""Notifications — /api/notifications/*"""
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required, role_required

notification_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notification_bp.get("")
@token_required
def my_notifications():
    cu = request.current_user
    db = get_db()
    if cu["role"] == "admin":
        rows = db.execute("SELECT * FROM notifications WHERE audience='admin' ORDER BY id DESC LIMIT 100").fetchall()
    else:
        rows = db.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 100",
                           (cu["sub"],)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})


@notification_bp.patch("/<int:nid>/read")
@token_required
def mark_read(nid):
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE id=?", (nid,))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Marked as read"})


@notification_bp.patch("/read-all")
@token_required
def mark_all_read():
    cu = request.current_user
    db = get_db()
    if cu["role"] == "admin":
        db.execute("UPDATE notifications SET is_read=1 WHERE audience='admin'")
    else:
        db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (cu["sub"],))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "All notifications marked as read"})
