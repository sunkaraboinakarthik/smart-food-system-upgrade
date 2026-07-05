"""Auth routes — /api/auth/*"""
import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, current_app
from database import get_db
from auth_utils import hash_password, verify_password, create_token, token_required, rate_limit
from utils.validators import validate_email, validate_phone, validate_password_strength, COUNTRY_CODES
from utils.otp import store_otp, verify_otp, send_email_otp, send_sms_otp
from utils.activity import log_activity, start_login_history, close_login_history, set_online, push_notification

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "profile_pics")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}


def user_safe(row):
    d = dict(row)
    d.pop("password", None)
    return d


@auth_bp.get("/country-codes")
def country_codes():
    return jsonify({"success": True, "data": COUNTRY_CODES})


# ── Register ────────────────────────────────────────────────────────────────
@auth_bp.post("/register")
@rate_limit(max_calls=10, window_seconds=300)
def register():
    data = request.get_json(silent=True) or {}
    name         = (data.get("name") or "").strip()
    username     = (data.get("username") or "").strip()
    email        = (data.get("email") or "").strip().lower()
    country_code = (data.get("country_code") or "+91").strip()
    phone        = (data.get("phone") or "").strip()
    password     = data.get("password") or ""
    confirm      = data.get("confirm_password") or data.get("confirmPassword") or ""
    dob          = (data.get("dob") or "").strip()
    gender       = (data.get("gender") or "").strip()

    if not name or not email or not password:
        return jsonify({"success": False, "message": "Full name, email and password are required"}), 400
    if not validate_email(email):
        return jsonify({"success": False, "message": "Please enter a valid email address"}), 400
    if phone:
        ok, msg = validate_phone(country_code, phone)
        if not ok:
            return jsonify({"success": False, "message": msg}), 400
    if confirm and password != confirm:
        return jsonify({"success": False, "message": "Passwords do not match"}), 400
    ok, msg = validate_password_strength(password)
    if not ok:
        return jsonify({"success": False, "message": msg}), 400

    db = get_db()
    if db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
        db.close()
        return jsonify({"success": False, "message": "Email already registered"}), 400
    if username and db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone():
        db.close()
        return jsonify({"success": False, "message": "Username already taken"}), 400

    db.execute(
        """INSERT INTO users(name, username, email, password, role, phone, country_code, dob, gender, is_active, email_verified)
           VALUES (?,?,?,?,?,?,?,?,?,1,0)""",
        (name, username, email, hash_password(password), "user", phone, country_code, dob, gender),
    )
    db.commit()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    db.close()

    # Registration flow requires email OTP verification before the account is fully active
    code = store_otp(email, "email_verify")
    send_email_otp(email, code, purpose="verify your SmartFood account")

    log_activity(user["id"], name, "register", f"New registration: {email}")
    push_notification(None, "admin", "New User Registered", f"{name} ({email}) just signed up", "info")

    return jsonify({
        "success": True,
        "message": "Registration successful. An OTP has been sent to your email — verify it to activate your account.",
        "data": {"user": user_safe(user), "otp_required": True},
    }), 201


@auth_bp.post("/verify-email-otp")
def verify_email_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code = (data.get("otp") or data.get("code") or "").strip()
    if not email or not code:
        return jsonify({"success": False, "message": "email and otp are required"}), 400
    if not verify_otp(email, "email_verify", code):
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400

    db = get_db()
    db.execute("UPDATE users SET email_verified=1 WHERE email=?", (email,))
    db.commit()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    db.close()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    token = create_token(user["id"], user["email"], user["role"], user["name"])
    log_activity(user["id"], user["name"], "email_verified", "Email OTP verified, account activated")
    return jsonify({"success": True, "message": "Account activated", "data": {"user": user_safe(user), "token": token}})


@auth_bp.post("/resend-otp")
@rate_limit(max_calls=5, window_seconds=300)
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    purpose = data.get("purpose", "email_verify")
    if not email:
        return jsonify({"success": False, "message": "email is required"}), 400
    code = store_otp(email, purpose)
    send_email_otp(email, code, purpose="verify your SmartFood account")
    return jsonify({"success": True, "message": "OTP resent"})


@auth_bp.post("/send-phone-otp")
@token_required
def send_phone_otp():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (request.current_user["sub"],)).fetchone()
    db.close()
    if not user or not user["phone"]:
        return jsonify({"success": False, "message": "No phone number on file"}), 400
    code = store_otp(user["phone"], "phone_verify")
    send_sms_otp(user["phone"], code)
    return jsonify({"success": True, "message": "OTP sent to phone"})


@auth_bp.post("/verify-phone-otp")
@token_required
def verify_phone_otp():
    data = request.get_json(silent=True) or {}
    code = (data.get("otp") or data.get("code") or "").strip()
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (request.current_user["sub"],)).fetchone()
    if not user or not verify_otp(user["phone"], "phone_verify", code):
        db.close()
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400
    db.execute("UPDATE users SET phone_verified=1 WHERE id=?", (user["id"],))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Phone number verified"})


# ── Login (email OR phone + password) ─────────────────────────────────────────
@auth_bp.post("/login")
@rate_limit(max_calls=15, window_seconds=300)
def login():
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    phone    = (data.get("phone") or "").strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember") or data.get("rememberMe"))

    if not (email or phone) or not password:
        return jsonify({"success": False, "message": "Email/phone and password are required"}), 400

    db = get_db()
    if email:
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    else:
        user = db.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()

    if not user or not verify_password(password, user["password"]):
        if user:
            db.execute("UPDATE users SET failed_login_count = failed_login_count + 1 WHERE id=?", (user["id"],))
            db.commit()
            start_login_history(user["id"], success=False)
        db.close()
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    if user["is_blocked"]:
        db.close()
        return jsonify({"success": False, "message": "Your account has been blocked by admin. Contact support."}), 403
    if not user["is_active"]:
        db.close()
        return jsonify({"success": False, "message": "Account is deactivated"}), 401
    if not user["email_verified"]:
        db.close()
        return jsonify({"success": False, "message": "Please verify your email OTP first", "otp_required": True}), 403

    db.execute("UPDATE users SET failed_login_count=0 WHERE id=?", (user["id"],))
    db.commit()
    db.close()

    token = create_token(user["id"], user["email"], user["role"], user["name"], remember=remember)
    start_login_history(user["id"], success=True)
    set_online(user["id"], True)
    log_activity(user["id"], user["name"], "login", "User logged in")
    push_notification(None, "admin", "New Login", f"{user['name']} logged in", "info")

    return jsonify({"success": True, "message": "Login successful", "data": {"user": user_safe(user), "token": token}})


@auth_bp.post("/logout")
@token_required
def logout():
    cu = request.current_user
    set_online(cu["sub"], False)
    close_login_history(cu["sub"])
    log_activity(cu["sub"], cu["name"], "logout", "User logged out")
    return jsonify({"success": True, "message": "Logged out"})


# ── Forgot password (Email -> OTP -> New password) ────────────────────────────
@auth_bp.post("/forgot-password")
@rate_limit(max_calls=5, window_seconds=300)
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"success": False, "message": "email is required"}), 400
    db = get_db()
    user = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
    db.close()
    # Always respond success to avoid leaking which emails are registered
    if user:
        code = store_otp(email, "forgot_password")
        send_email_otp(email, code, purpose="reset your SmartFood password")
    return jsonify({"success": True, "message": "If that email is registered, an OTP has been sent"})


@auth_bp.post("/reset-password")
@rate_limit(max_calls=10, window_seconds=300)
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    code  = (data.get("otp") or data.get("code") or "").strip()
    new_pw = data.get("newPassword") or data.get("new_password") or ""

    if not email or not code or not new_pw:
        return jsonify({"success": False, "message": "email, otp and newPassword are required"}), 400
    ok, msg = validate_password_strength(new_pw)
    if not ok:
        return jsonify({"success": False, "message": msg}), 400
    if not verify_otp(email, "forgot_password", code):
        return jsonify({"success": False, "message": "Invalid or expired OTP"}), 400

    db = get_db()
    db.execute("UPDATE users SET password=? WHERE email=?", (hash_password(new_pw), email))
    db.commit()
    user = db.execute("SELECT id, name FROM users WHERE email=?", (email,)).fetchone()
    db.close()
    if user:
        log_activity(user["id"], user["name"], "password_reset", "Password reset via forgot-password OTP flow")
    return jsonify({"success": True, "message": "Password reset successful — please log in"})


# ── Profile ────────────────────────────────────────────────────────────────────
@auth_bp.get("/me")
@token_required
def me():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (request.current_user["sub"],)).fetchone()
    db.close()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    return jsonify({"success": True, "data": user_safe(user)})


@auth_bp.put("/me")
@token_required
def update_me():
    data    = request.get_json(silent=True) or {}
    updates = []
    params  = []
    for field in ("name", "address", "phone", "username", "dob", "gender", "country_code"):
        if field in data:
            updates.append(f"{field}=?")
            params.append(data[field])
    if not updates:
        return jsonify({"success": False, "message": "Nothing to update"}), 400
    params.append(request.current_user["sub"])
    db = get_db()
    db.execute(f"UPDATE users SET {', '.join(updates)} WHERE id=?", params)
    db.commit()
    user = db.execute("SELECT * FROM users WHERE id=?", (request.current_user["sub"],)).fetchone()
    db.close()
    log_activity(user["id"], user["name"], "profile_update", "Updated profile details")
    return jsonify({"success": True, "message": "Profile updated", "data": user_safe(user)})


@auth_bp.post("/me/profile-picture")
@token_required
def upload_profile_picture():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "file is required"}), 400
    file = request.files["file"]
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXT:
        return jsonify({"success": False, "message": "Only image files are allowed (png/jpg/jpeg/gif/webp)"}), 400

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    user_id = request.current_user["sub"]
    filename = secure_filename(f"user_{user_id}.{ext}")
    file.save(os.path.join(UPLOAD_DIR, filename))

    url_path = f"/uploads/profile_pics/{filename}"
    db = get_db()
    db.execute("UPDATE users SET profile_pic=? WHERE id=?", (url_path, user_id))
    db.commit()
    db.close()
    return jsonify({"success": True, "message": "Profile picture updated", "data": {"profile_pic": url_path}})


@auth_bp.post("/change-password")
@token_required
def change_password():
    data    = request.get_json(silent=True) or {}
    current = data.get("currentPassword") or ""
    new_pw  = data.get("newPassword") or ""
    if not current or not new_pw:
        return jsonify({"success": False, "message": "currentPassword and newPassword required"}), 400
    ok, msg = validate_password_strength(new_pw)
    if not ok:
        return jsonify({"success": False, "message": msg}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (request.current_user["sub"],)).fetchone()
    if not verify_password(current, user["password"]):
        db.close()
        return jsonify({"success": False, "message": "Current password is incorrect"}), 400
    db.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_pw), user["id"]))
    db.commit()
    db.close()
    log_activity(user["id"], user["name"], "password_change", "Password changed from account settings")
    return jsonify({"success": True, "message": "Password changed successfully"})
