"""
Real-time layer — Flask-SocketIO instance shared across the app.

The admin dashboard joins the "admin_room" and receives live events:
 register, login, logout, cart_update, order_placed, payment_update,
 order_status_update, review_added — exactly the "Live User Activity" feed
 requested in the spec.

If flask-socketio isn't installed, the app still runs fine (emit_event becomes
a no-op) so the REST API is never blocked by the real-time layer.
"""
try:
    from flask_socketio import SocketIO, join_room
    socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")
    SOCKETIO_AVAILABLE = True
except ImportError:
    socketio = None
    SOCKETIO_AVAILABLE = False

ADMIN_ROOM = "admin_room"


def init_socketio(app):
    if not SOCKETIO_AVAILABLE:
        print("⚠️  flask-socketio not installed — real-time admin feed disabled. "
              "Run: pip install flask-socketio")
        return None
    socketio.init_app(app)

    @socketio.on("join_admin")
    def _join_admin(data=None):
        join_room(ADMIN_ROOM)

    return socketio


def emit_event(event: str, payload: dict):
    """Push a live event to every connected admin dashboard."""
    if not SOCKETIO_AVAILABLE:
        return
    try:
        socketio.emit(event, payload, room=ADMIN_ROOM)
    except Exception as e:
        print(f"⚠️  Realtime emit failed: {e}")
