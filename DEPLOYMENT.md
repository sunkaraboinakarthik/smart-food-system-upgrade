# Deployment Notes

This project ships as a Flask + SQLite backend and a static HTML/CSS/JS
frontend. Below are practical notes for taking it beyond a local demo.

## Backend

**Development (what you get out of the box)**
```bash
cd smartfood-backend
pip install -r requirements.txt
python app.py
```

**Production checklist**
1. **WSGI server** — don't use `python app.py` (Werkzeug's dev server) in
   production. Use gunicorn with the eventlet/gevent worker so Flask-SocketIO
   still works:
   ```bash
   pip install gunicorn eventlet
   gunicorn -k eventlet -w 1 app:app --bind 0.0.0.0:5000
   ```
   (SocketIO with the threading async_mode used here needs a single worker
   process, or a message queue like Redis if you need multiple workers.)
2. **Database** — SQLite is fine for a demo/small deployment. For real
   production scale, migrate to PostgreSQL: swap `database.py`'s
   `sqlite3.connect` for `psycopg2`/SQLAlchemy and adjust the `datetime('now')`
   defaults (Postgres uses `now()`).
3. **Environment variables** — set real values for `SECRET_KEY`, `SMTP_*`,
   `SMS_API_KEY`, `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET` (see `.env.example`).
   Never commit `.env` — it's already in `.gitignore`.
4. **HTTPS** — put the app behind a reverse proxy (nginx, Caddy) with a real
   TLS certificate. Don't expose the Flask/gunicorn port directly.
5. **CORS** — the current `Access-Control-Allow-Origin: *` is convenient for
   development. Restrict it to your actual frontend domain in production
   (edit `add_security_and_cors_headers` in `app.py`).
6. **Rate limiting** — the built-in limiter in `auth_utils.py` is in-memory
   and per-process; behind multiple workers/instances, replace it with
   Flask-Limiter + Redis.
7. **File uploads** — profile pictures are saved to `smartfood-backend/uploads/`.
   In production, point this at persistent storage (S3, GCS, a mounted volume)
   rather than local disk on an ephemeral container.

## Frontend

Static files — deploy `index/` to any static host (Netlify, Vercel, S3+CloudFront,
nginx). Before deploying, set the API base URL to your real backend, e.g. in
`index/index.html` (and any other entry page) before `js/api.js` loads:

```html
<script>window.SMARTFOOD_API_BASE = 'https://api.yourdomain.com/api';</script>
<script src="js/api.js"></script>
```

## Real-time (Socket.IO)

The admin live feed connects to the same host as `SMARTFOOD_API_BASE` (minus
`/api`). Make sure your reverse proxy passes through WebSocket upgrade
headers if you put nginx in front of the backend:

```nginx
location /socket.io/ {
    proxy_pass http://127.0.0.1:5000/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

## Cloud options mentioned in the original spec

- **Render / Railway** — easiest for this stack; both support gunicorn +
  a persistent disk for SQLite, or a managed Postgres add-on.
- **AWS / Azure** — works, but plan for managed Postgres (RDS/Azure DB),
  S3/Blob storage for uploads, and a load balancer with sticky sessions if
  you scale Socket.IO beyond one instance.
