"""
SmartFood Auth Utilities
JWT (HS256) + PBKDF2 password hashing — stdlib only
"""
import jwt
import hashlib
import os
import secrets
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.environ.get("SECRET_KEY", "smartfood_super_secret_2024_!@#XYZ")
JWT_ALGO   = "HS256"
JWT_EXP_DAYS = 7
JWT_EXP_DAYS_REMEMBER = 30


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_token(user_id: int, email: str, role: str, name: str, remember: bool = False) -> str:
    days = JWT_EXP_DAYS_REMEMBER if remember else JWT_EXP_DAYS
    payload = {
        "sub":   user_id,
        "email": email,
        "role":  role,
        "name":  name,
        "exp":   datetime.now(timezone.utc) + timedelta(days=days),
        "iat":   datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGO)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGO])
    except Exception:
        return None


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100_000)
    return f"{salt}:{hashed.hex()}"


def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, stored_hash = stored.split(":", 1)
        attempt = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 100_000)
        return attempt.hex() == stored_hash
    except Exception:
        return False


# ── Decorators ────────────────────────────────────────────────────────────────

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
        payload = decode_token(token) if token else None
        if not payload:
            return jsonify({"success": False, "message": "Unauthorized — invalid or missing token"}), 401
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated


_rate_buckets: dict = {}

def rate_limit(max_calls: int = 10, window_seconds: int = 60):
    """Lightweight per-IP+route rate limiter. Good enough for a single-process
    demo/small-scale deployment; swap for Flask-Limiter + Redis at real scale."""
    import time as _time

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = f"{request.remote_addr}:{f.__name__}"
            now = _time.time()
            bucket = _rate_buckets.setdefault(key, [])
            bucket[:] = [t for t in bucket if now - t < window_seconds]
            if len(bucket) >= max_calls:
                return jsonify({"success": False, "message": "Too many requests, please slow down"}), 429
            bucket.append(now)
            return f(*args, **kwargs)
        return decorated
    return decorator


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            if request.current_user.get("role") not in roles:
                return jsonify({"success": False, "message": f"Forbidden — requires role: {' or '.join(roles)}"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator
