# SmartFood — Upgraded Food Ordering Platform

A Flask + SQLite backend and HTML/CSS/JS frontend for a food delivery platform,
upgraded from the original student-project baseline with real authentication,
real-time admin monitoring, and a much larger feature set.

This README is honest about what's fully wired end-to-end versus what's a
solid backend foundation still waiting on frontend wiring — see
**"Known limitations / next steps"** at the bottom before you assume everything
is 100% connected.

---

## Quick start

### 1. Backend

```bash
cd smartfood-backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env   # edit values if you want real email/SMS/Razorpay
python app.py
```

The server starts on `http://localhost:5000` and prints demo credentials.
On first run it creates `smartfood.db` (SQLite) and seeds demo data.

### 2. Frontend

The frontend is static HTML/CSS/JS — no build step. Serve the `index/` folder
with any static file server, e.g.:

```bash
cd index
python3 -m http.server 8080
```

Then open `http://localhost:8080`. The frontend calls the backend at
`http://localhost:5000/api` by default — override this by setting
`window.SMARTFOOD_API_BASE` before `js/api.js` loads if you deploy the
backend elsewhere.

### Demo accounts

| Role     | Email                       | Password      |
|----------|------------------------------|---------------|
| Admin    | admin@smartfood.com         | admin123      |
| Delivery | delivery@smartfood.com      | delivery123   |
| Customer | user@smartfood.com          | user123       |

These demo accounts are pre-verified (`email_verified=1`) so they can log in
immediately. New signups go through the real OTP flow.

---

## What's implemented in this upgrade

### Authentication & security
- Registration with full name, optional username, email, phone + country-code
  selector (🇮🇳+91, 🇺🇸+1, 🇬🇧+44, 🇦🇪+971, 🇨🇦+1, 🇦🇺+61, 🇸🇬+65, 🇩🇪+49),
  password + confirm password, optional DOB/gender, optional profile picture
- Server-side validation: email format, per-country phone digit rules, strong
  password rules (8+ chars, upper/lower/number/symbol)
- Email OTP verification required before an account is active (console/log
  output in dev mode, real SMTP if you configure `.env`)
- Optional phone OTP verification endpoint (SMS gateway pluggable)
- Forgot password: email → OTP → new password
- JWT auth (7-day default, 30-day with "Remember me"), PBKDF2-HMAC password
  hashing, role-based access control (user / admin / delivery)
- Rate limiting on auth endpoints, security response headers, basic XSS-safe
  text sanitization helpers

### Real-time admin monitoring
- Flask-SocketIO backend broadcasts live events: registrations, logins,
  logouts, cart changes, orders placed, payments, status changes, reviews
- Every action is also written to an `activity_logs` audit table
- Admin dashboard live activity feed connects over WebSockets and updates
  without a page refresh
- Online-user counter, login history (device/browser/IP), audit logs

### Customer / Admin / Delivery features
- Wishlist, saved addresses (multiple, with default), saved-for-later cart
  items, coupons (create/edit/delete/usage limits), reviews with admin replies
- Inventory tracking with low-stock alerts and admin notifications
- Notifications table for both customer and admin audiences
- Expanded admin dashboard: total/online users, today's registrations, full
  order-status breakdown, today/monthly/total revenue, best/least selling
  items, top customers, revenue chart, low-stock alerts
- Order lifecycle: place, cancel, reorder, printable invoice, delivery
  accept/reject, status history
- Razorpay payment integration (create-order + signature verification) and
  Cash on Delivery, both recorded in a `payments` table with transaction IDs
  and status. Runs in a safe sandbox mode with no live keys configured.

### Database
See `smartfood-backend/schema.sql` for the full generated schema. New tables:
`wishlist`, `addresses`, `notifications`, `activity_logs`, `login_history`,
`inventory`, `payments`, `otp_codes`, plus new columns on `users` and expanded
`promo_codes`/`reviews`/`delivery_agents`.

---

## Known limitations / next steps

Being upfront rather than overstating what's here:

- **Frontend wiring is partial.** The original project's `menu.html`,
  `cart.html`, `dashboard.html`, `delivery-dashboard.html`, and
  `track-order.html` still run on the original localStorage-based demo data
  (not the real backend). **Auth (register/login/logout/forgot password) and
  the admin dashboard (stats, orders, live feed) are fully wired to the real
  API** — those are the pieces this upgrade focused on. Wiring the remaining
  customer-facing pages (menu browsing, cart, checkout, order tracking) to
  the new `/api/cart`, `/api/orders`, `/api/wishlist`, `/api/addresses`,
  `/api/payments` endpoints is the natural next step, and the backend is
  ready for it.
- **No live Stripe/PayPal, real SMS gateway, trained AI chatbot, or
  multi-language (i18n) support.** Razorpay + COD are implemented; the
  chatbot on the site is the original scripted demo widget, not an LLM.
- **No PWA manifest / mobile app.** Out of scope for a backend/API upgrade
  like this one.
- **SQLite, not Postgres/MySQL**, and the dev server (not gunicorn/nginx) —
  fine for a demo or small deployment, not for real production scale. See
  `DEPLOYMENT.md` for notes on hardening this further.

## Project structure

```
smartfood-backend/
  app.py                 # Flask app, blueprint registration, SocketIO init
  database.py             # Schema + safe migrations for existing DBs
  seeder.py                # Demo data
  auth_utils.py            # JWT, password hashing, rate limiting, RBAC
  utils/
    validators.py          # Email/phone/password validation
    otp.py                 # OTP generation + email/SMS sending (pluggable)
    activity.py             # Audit logging + live event helper
    realtime.py             # Flask-SocketIO wrapper
  routes/                  # One blueprint per feature area
  schema.sql               # Generated full DB schema
  requirements.txt
  .env.example

index/                    # Static frontend (HTML/CSS/JS, no build step)
  js/api.js                # Fetch wrapper hitting the real backend
  js/auth.js                # Real auth client (register/login/OTP/logout)
  js/admin.js                # Admin dashboard wired to real API + Socket.IO
  js/theme.js                 # Dark/light mode toggle
  ...
```

See `DEPLOYMENT.md` for deployment notes.
