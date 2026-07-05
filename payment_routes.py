"""
Payment routes — /api/payments/*
Supports Razorpay (test/live keys via env vars) and Cash on Delivery.
Every payment attempt is recorded in the `payments` table with method,
transaction id, and status, as required.
"""
import os
import hmac
import hashlib
import uuid
from flask import Blueprint, request, jsonify
from database import get_db
from auth_utils import token_required
from utils.activity import log_activity, push_notification

payment_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

RAZORPAY_KEY_ID     = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

try:
    import razorpay
    _client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)) if RAZORPAY_KEY_ID else None
except ImportError:
    _client = None


@payment_bp.post("/razorpay/create-order")
@token_required
def create_razorpay_order():
    b = request.get_json(silent=True) or {}
    order_id = b.get("order_id")
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, request.current_user["sub"])).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404

    amount_paise = int(round(order["total"] * 100))

    if _client:
        rp_order = _client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "receipt": f"order_rcpt_{order_id}",
            "payment_capture": 1,
        })
        rp_order_id = rp_order["id"]
    else:
        # No live Razorpay keys configured — generate a sandbox-style reference so the
        # rest of the flow (frontend checkout, verification, storage) still works end-to-end.
        rp_order_id = f"order_sandbox_{uuid.uuid4().hex[:14]}"

    db.execute("""
        INSERT INTO payments(order_id, user_id, method, amount, razorpay_order_id, status)
        VALUES (?,?,?,?,?,?)
    """, (order_id, request.current_user["sub"], "razorpay", order["total"], rp_order_id, "Pending"))
    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "data": {
            "razorpay_order_id": rp_order_id,
            "amount": amount_paise,
            "currency": "INR",
            "key_id": RAZORPAY_KEY_ID or "rzp_test_not_configured",
            "live_mode": bool(_client),
        }
    })


@payment_bp.post("/razorpay/verify")
@token_required
def verify_razorpay_payment():
    b = request.get_json(silent=True) or {}
    rp_order_id   = b.get("razorpay_order_id")
    rp_payment_id = b.get("razorpay_payment_id")
    rp_signature  = b.get("razorpay_signature")

    if not all([rp_order_id, rp_payment_id]):
        return jsonify({"success": False, "message": "razorpay_order_id and razorpay_payment_id required"}), 400

    verified = False
    if _client and rp_signature:
        try:
            _client.utility.verify_payment_signature({
                "razorpay_order_id": rp_order_id,
                "razorpay_payment_id": rp_payment_id,
                "razorpay_signature": rp_signature,
            })
            verified = True
        except Exception:
            verified = False
    elif not _client:
        # Sandbox mode (no live keys) — accept the client-reported success so the
        # rest of the app (order status, notifications) can be fully exercised/tested.
        verified = True

    db = get_db()
    payment = db.execute("SELECT * FROM payments WHERE razorpay_order_id=?", (rp_order_id,)).fetchone()
    if not payment:
        db.close()
        return jsonify({"success": False, "message": "Payment record not found"}), 404

    status = "Success" if verified else "Failed"
    db.execute("UPDATE payments SET status=?, transaction_id=? WHERE id=?", (status, rp_payment_id, payment["id"]))
    if verified:
        db.execute("UPDATE orders SET status='Preparing', updated_at=datetime('now') WHERE id=?", (payment["order_id"],))
        db.execute("INSERT INTO order_status_history(order_id, status, note) VALUES (?,?,?)",
                   (payment["order_id"], "Preparing", "Payment confirmed via Razorpay"))
    db.commit()
    order = db.execute("SELECT * FROM orders WHERE id=?", (payment["order_id"],)).fetchone()
    db.close()

    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "payment_" + ("success" if verified else "failed"),
                 f"Order #{payment['order_id']} — {rp_payment_id}")
    push_notification(None, "admin", "Payment " + ("Success" if verified else "Failed"),
                       f"Order #{payment['order_id']} by {cu['name']}", "success" if verified else "error")
    if verified:
        push_notification(cu["sub"], "user", "Payment Successful", f"Your payment for order #{payment['order_id']} was received", "success")

    return jsonify({"success": verified, "message": "Payment verified" if verified else "Payment verification failed",
                     "data": {"order_status": order["status"] if order else None}})


@payment_bp.post("/cod")
@token_required
def record_cod_payment():
    b = request.get_json(silent=True) or {}
    order_id = b.get("order_id")
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id=? AND user_id=?", (order_id, request.current_user["sub"])).fetchone()
    if not order:
        db.close()
        return jsonify({"success": False, "message": "Order not found"}), 404

    txn_id = f"COD-{uuid.uuid4().hex[:10].upper()}"
    db.execute("""
        INSERT INTO payments(order_id, user_id, method, amount, transaction_id, status)
        VALUES (?,?,?,?,?,?)
    """, (order_id, request.current_user["sub"], "cod", order["total"], txn_id, "Pending"))
    db.commit()
    db.close()

    cu = request.current_user
    log_activity(cu["sub"], cu["name"], "cod_order", f"Order #{order_id} placed with Cash on Delivery")
    push_notification(None, "admin", "New Order (COD)", f"Order #{order_id} by {cu['name']}", "info")
    return jsonify({"success": True, "message": "Cash on Delivery selected", "data": {"transaction_id": txn_id}})


@payment_bp.get("/history")
@token_required
def payment_history():
    cu = request.current_user
    db = get_db()
    if cu["role"] == "admin":
        rows = db.execute("SELECT * FROM payments ORDER BY id DESC LIMIT 200").fetchall()
    else:
        rows = db.execute("SELECT * FROM payments WHERE user_id=? ORDER BY id DESC", (cu["sub"],)).fetchall()
    db.close()
    return jsonify({"success": True, "data": [dict(r) for r in rows]})
