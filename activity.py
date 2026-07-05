"""
Central activity/audit logger.

Every meaningful user action (register, login, logout, browse, cart change,
order placed, payment, cancel, profile update, delivery completed, admin
actions) is written to activity_logs AND pushed live to the admin dashboard
over WebSockets, satisfying the "real-time admin monitoring" requirement.
"""
from flask import request as flask_request
from database import get_db
from utils.realtime import emit_event


def client_ip() -> str:
    try:
        fwd = flask_request.headers.get("X-Forwarded-For")
        return (fwd.split(",")[0].strip() if fwd else flask_request.remote_addr) or "unknown"
    except Exception:
        return "unknown"


def log_activity(user_id, user_name: str, action: str, details: str = ""):
    db = get_db()
    ip = client_ip()
    db.execute(
        "INSERT INTO activity_logs(user_id, user_name, action, details, ip_address) VALUES (?,?,?,?,?)",
        (user_id, user_name, action, details, ip),
    )
    db.commit()
    row = db.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 1").fetchone()
    db.close()

    emit_event("activity", {
        "id": row["id"],
        "user_id": user_id,
        "user_name": user_name,
        "action": action,
        "details": details,
        "ip_address": ip,
        "created_at": row["created_at"],
    })


def start_login_history(user_id: int, success: bool = True):
    ua = flask_request.headers.get("User-Agent", "")
    device = "Mobile" if any(k in ua for k in ("Mobi", "Android", "iPhone")) else "Desktop"
    browser = next((b for b in ("Chrome", "Firefox", "Safari", "Edge", "Opera") if b in ua), "Unknown")
    db = get_db()
    db.execute(
        "INSERT INTO login_history(user_id, device, browser, ip_address, success) VALUES (?,?,?,?,?)",
        (user_id, device, browser, client_ip(), 1 if success else 0),
    )
    db.commit()
    row_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return row_id


def close_login_history(user_id: int):
    db = get_db()
    db.execute(
        """UPDATE login_history SET logout_time=datetime('now')
           WHERE id = (SELECT id FROM login_history WHERE user_id=? AND logout_time=''
                       ORDER BY id DESC LIMIT 1)""",
        (user_id,),
    )
    db.commit()
    db.close()


def set_online(user_id: int, online: bool):
    db = get_db()
    db.execute(
        "UPDATE users SET is_online=?, last_seen=datetime('now') WHERE id=?",
        (1 if online else 0, user_id),
    )
    db.commit()
    row = db.execute("SELECT COUNT(*) c FROM users WHERE is_online=1").fetchone()
    online_count = row["c"]
    db.close()
    emit_event("online_count", {"online_users": online_count})


def push_notification(user_id, audience: str, title: str, message: str = "", ntype: str = "info"):
    db = get_db()
    db.execute(
        "INSERT INTO notifications(user_id, audience, title, message, type) VALUES (?,?,?,?,?)",
        (user_id, audience, title, message, ntype),
    )
    db.commit()
    row = db.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 1").fetchone()
    db.close()
    emit_event("notification", dict(row))
