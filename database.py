"""
SmartFood Database Layer
SQLite with raw SQL — no ORM needed
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "smartfood.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _add_column_if_missing(c, table, column, coldef):
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coldef}")


def init_db():
    conn = get_db()
    c = conn.cursor()

    # ── Users ──────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user',
            phone       TEXT    DEFAULT '',
            address     TEXT    DEFAULT '',
            is_active   INTEGER DEFAULT 1,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)
    # New profile / security columns (added safely if upgrading an existing DB)
    for col, coldef in [
        ("username",           "TEXT DEFAULT ''"),
        ("country_code",       "TEXT DEFAULT '+91'"),
        ("dob",                "TEXT DEFAULT ''"),
        ("gender",             "TEXT DEFAULT ''"),
        ("profile_pic",        "TEXT DEFAULT ''"),
        ("email_verified",     "INTEGER DEFAULT 0"),
        ("phone_verified",     "INTEGER DEFAULT 0"),
        ("is_online",          "INTEGER DEFAULT 0"),
        ("last_seen",          "TEXT DEFAULT ''"),
        ("is_blocked",         "INTEGER DEFAULT 0"),
        ("failed_login_count", "INTEGER DEFAULT 0"),
    ]:
        _add_column_if_missing(c, "users", col, coldef)

    # ── Restaurants ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS restaurants (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            cuisine       TEXT    DEFAULT '',
            rating        REAL    DEFAULT 4.0,
            delivery_time TEXT    DEFAULT '30-40 min',
            min_order     INTEGER DEFAULT 200,
            img           TEXT    DEFAULT '',
            emoji         TEXT    DEFAULT '🍽️',
            discount      TEXT    DEFAULT '',
            is_open       INTEGER DEFAULT 1,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Food Items ─────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS food_items (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
            name          TEXT    NOT NULL,
            price         REAL    NOT NULL,
            description   TEXT    DEFAULT '',
            img           TEXT    DEFAULT '',
            emoji         TEXT    DEFAULT '🍽️',
            type          TEXT    DEFAULT 'veg',
            category      TEXT    DEFAULT 'Main',
            is_popular    INTEGER DEFAULT 0,
            is_available  INTEGER DEFAULT 1,
            rating        REAL    DEFAULT 4.0,
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Orders ─────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            user_name       TEXT    DEFAULT '',
            user_address    TEXT    DEFAULT '',
            restaurant_id   INTEGER REFERENCES restaurants(id),
            restaurant_name TEXT    DEFAULT '',
            payment_method  TEXT    NOT NULL,
            subtotal        REAL    DEFAULT 0,
            delivery_fee    REAL    DEFAULT 0,
            discount        REAL    DEFAULT 0,
            promo_code      TEXT    DEFAULT '',
            total           REAL    DEFAULT 0,
            status          TEXT    DEFAULT 'Pending',
            agent_id        TEXT    DEFAULT '',
            agent_name      TEXT    DEFAULT '',
            agent_phone     TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now')),
            updated_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Order Items ────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id    INTEGER NOT NULL REFERENCES orders(id),
            food_item_id INTEGER,
            name        TEXT    NOT NULL,
            price       REAL    NOT NULL,
            quantity    INTEGER NOT NULL DEFAULT 1,
            emoji       TEXT    DEFAULT '',
            img         TEXT    DEFAULT ''
        )
    """)

    # ── Order Status History ───────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS order_status_history (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id),
            status     TEXT    NOT NULL,
            note       TEXT    DEFAULT '',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Cart ───────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            food_item_id INTEGER NOT NULL REFERENCES food_items(id),
            quantity     INTEGER DEFAULT 1,
            saved_for_later INTEGER DEFAULT 0,
            UNIQUE(user_id, food_item_id)
        )
    """)
    _add_column_if_missing(c, "cart", "saved_for_later", "INTEGER DEFAULT 0")

    # ── Promo Codes / Coupons ──────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS promo_codes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            code         TEXT    NOT NULL UNIQUE,
            type         TEXT    NOT NULL,
            value        REAL    NOT NULL,
            min_order    REAL    DEFAULT 0,
            description  TEXT    DEFAULT '',
            is_active    INTEGER DEFAULT 1,
            expires_at   TEXT    DEFAULT '',
            usage_limit  INTEGER DEFAULT 0,
            used_count   INTEGER DEFAULT 0
        )
    """)
    for col, coldef in [("usage_limit", "INTEGER DEFAULT 0"), ("used_count", "INTEGER DEFAULT 0")]:
        _add_column_if_missing(c, "promo_codes", col, coldef)

    # ── Delivery Agents ────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS delivery_agents (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_code   TEXT    NOT NULL UNIQUE,
            name         TEXT    NOT NULL,
            phone        TEXT    DEFAULT '',
            rating       REAL    DEFAULT 5.0,
            is_available INTEGER DEFAULT 1,
            user_id      INTEGER REFERENCES users(id)
        )
    """)
    _add_column_if_missing(c, "delivery_agents", "user_id", "INTEGER REFERENCES users(id)")

    # ── Reviews ────────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurant_id INTEGER NOT NULL REFERENCES restaurants(id),
            user_id       INTEGER NOT NULL REFERENCES users(id),
            user_name     TEXT    DEFAULT '',
            rating        REAL    NOT NULL,
            comment       TEXT    DEFAULT '',
            admin_reply   TEXT    DEFAULT '',
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)
    _add_column_if_missing(c, "reviews", "admin_reply", "TEXT DEFAULT ''")

    # ── Wishlist ───────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            food_item_id INTEGER NOT NULL REFERENCES food_items(id),
            created_at   TEXT    DEFAULT (datetime('now')),
            UNIQUE(user_id, food_item_id)
        )
    """)

    # ── Addresses ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS addresses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            label       TEXT    DEFAULT 'Home',
            line1       TEXT    NOT NULL,
            line2       TEXT    DEFAULT '',
            city        TEXT    DEFAULT '',
            state       TEXT    DEFAULT '',
            pincode     TEXT    DEFAULT '',
            is_default  INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Notifications ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            audience   TEXT    DEFAULT 'user',
            title      TEXT    NOT NULL,
            message    TEXT    DEFAULT '',
            type       TEXT    DEFAULT 'info',
            is_read    INTEGER DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Activity Logs (audit trail, drives live admin feed) ────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER REFERENCES users(id),
            user_name  TEXT    DEFAULT '',
            action     TEXT    NOT NULL,
            details    TEXT    DEFAULT '',
            ip_address TEXT    DEFAULT '',
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Login History ──────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS login_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            login_time  TEXT    DEFAULT (datetime('now')),
            logout_time TEXT    DEFAULT '',
            device      TEXT    DEFAULT '',
            browser     TEXT    DEFAULT '',
            ip_address  TEXT    DEFAULT '',
            success     INTEGER DEFAULT 1
        )
    """)

    # ── Inventory ──────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name     TEXT    NOT NULL UNIQUE,
            unit          TEXT    DEFAULT 'kg',
            quantity      REAL    DEFAULT 0,
            low_stock_at  REAL    DEFAULT 5,
            updated_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Payments ───────────────────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id          INTEGER NOT NULL REFERENCES orders(id),
            user_id           INTEGER NOT NULL REFERENCES users(id),
            method            TEXT    NOT NULL,
            amount            REAL    NOT NULL,
            transaction_id    TEXT    DEFAULT '',
            razorpay_order_id TEXT    DEFAULT '',
            status            TEXT    DEFAULT 'Pending',
            created_at        TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── OTP Codes (email / phone verification, forgot password) ────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT    NOT NULL,
            purpose    TEXT    NOT NULL,
            code       TEXT    NOT NULL,
            expires_at TEXT    NOT NULL,
            used       INTEGER DEFAULT 0,
            created_at TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Indexes ────────────────────────────────────────────────────────────────
    c.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_food_items_restaurant ON food_items(restaurant_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_login_history_user ON login_history(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_wishlist_user ON wishlist(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_otp_identifier ON otp_codes(identifier, purpose)")

    conn.commit()
    conn.close()
    print("✅ Database tables created/upgraded")
