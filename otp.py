"""
OTP utilities — email/phone verification and forgot-password codes.

Delivery is pluggable:
- If SMTP_HOST/SMTP_USER/SMTP_PASS are set in the environment, a real email is sent.
- Otherwise the OTP is printed to the server console/log (clearly marked "DEV MODE"),
  which is exactly how most student/demo projects run without paid SMS/email credits.
  Swap in a real provider (SendGrid, SES, Twilio, MSG91, etc.) by editing send_email_otp /
  send_sms_otp below — the rest of the app never needs to change.
"""
import os
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from database import get_db

OTP_EXPIRY_MINUTES = 10


def generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def store_otp(identifier: str, purpose: str) -> str:
    """identifier = email or phone. purpose = 'email_verify' | 'phone_verify' | 'forgot_password'"""
    code = generate_otp()
    expires_at = (datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    db = get_db()
    db.execute("UPDATE otp_codes SET used=1 WHERE identifier=? AND purpose=? AND used=0", (identifier, purpose))
    db.execute(
        "INSERT INTO otp_codes(identifier, purpose, code, expires_at) VALUES (?,?,?,?)",
        (identifier, purpose, code, expires_at),
    )
    db.commit()
    db.close()
    return code


def verify_otp(identifier: str, purpose: str, code: str) -> bool:
    db = get_db()
    row = db.execute(
        """SELECT * FROM otp_codes WHERE identifier=? AND purpose=? AND used=0
           ORDER BY id DESC LIMIT 1""",
        (identifier, purpose),
    ).fetchone()
    if not row:
        db.close()
        return False
    if row["code"] != code:
        db.close()
        return False
    if datetime.fromisoformat(row["expires_at"]) < datetime.utcnow():
        db.close()
        return False
    db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (row["id"],))
    db.commit()
    db.close()
    return True


def send_email_otp(email: str, code: str, purpose: str = "verify your account"):
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    subject = "SmartFood — Your OTP Code"
    body = f"Your SmartFood OTP to {purpose} is: {code}\nThis code expires in {OTP_EXPIRY_MINUTES} minutes."

    if smtp_host and smtp_user and smtp_pass:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [email], msg.as_string())
            return
        except Exception as e:
            print(f"⚠️  SMTP send failed ({e}), falling back to console output")

    # DEV MODE fallback — no SMTP configured
    print(f"\n📧  [DEV MODE — no SMTP configured] OTP email to {email}: {code}  (purpose: {purpose})\n")


def send_sms_otp(phone: str, code: str):
    sms_key = os.environ.get("SMS_API_KEY")
    if sms_key:
        # Plug in Twilio / MSG91 / any SMS gateway here using sms_key.
        print(f"📱  [SMS provider configured but not wired up] Would send OTP {code} to {phone}")
        return
    print(f"\n📱  [DEV MODE — no SMS gateway configured] OTP SMS to {phone}: {code}\n")
