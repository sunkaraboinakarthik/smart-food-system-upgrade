"""
Input validators — email, phone (per country), password strength.
Used by registration, profile update, and forgot-password flows.
"""
import re

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

# digit-count rules per supported country code
PHONE_RULES = {
    "+91":  (10, 10),   # India
    "+1":   (10, 10),   # USA / Canada
    "+44":  (10, 10),   # UK (national significant number, ignoring leading 0)
    "+971": (9, 9),     # UAE
    "+61":  (9, 9),     # Australia
    "+65":  (8, 8),     # Singapore
    "+49":  (10, 11),   # Germany
}

COUNTRY_CODES = [
    {"code": "+91",  "country": "India",     "flag": "🇮🇳"},
    {"code": "+1",   "country": "USA",       "flag": "🇺🇸"},
    {"code": "+44",  "country": "UK",        "flag": "🇬🇧"},
    {"code": "+971", "country": "UAE",       "flag": "🇦🇪"},
    {"code": "+1",   "country": "Canada",    "flag": "🇨🇦"},
    {"code": "+61",  "country": "Australia", "flag": "🇦🇺"},
    {"code": "+65",  "country": "Singapore", "flag": "🇸🇬"},
    {"code": "+49",  "country": "Germany",   "flag": "🇩🇪"},
]


def validate_email(email: str) -> bool:
    if not email or "@" not in email:
        return False
    return bool(EMAIL_RE.match(email))


def validate_phone(country_code: str, phone: str) -> tuple[bool, str]:
    phone = (phone or "").strip()
    if not phone.isdigit():
        return False, "Phone number must contain digits only"
    lo, hi = PHONE_RULES.get(country_code, (7, 15))
    if not (lo <= len(phone) <= hi):
        if lo == hi:
            return False, f"Phone number for {country_code} must be exactly {lo} digits"
        return False, f"Phone number for {country_code} must be {lo}-{hi} digits"
    return True, ""


def validate_password_strength(password: str) -> tuple[bool, str]:
    if len(password or "") < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        return False, "Password must contain at least one special character"
    return True, ""


def sanitize_text(value: str, max_len: int = 500) -> str:
    """Basic XSS-safe cleanup for freeform text stored/echoed back (reviews, notes, etc)."""
    if not value:
        return ""
    value = value.strip()[:max_len]
    value = value.replace("<", "&lt;").replace(">", "&gt;")
    return value
