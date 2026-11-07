# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Python Ad Network - Server (Flask)

Improvements over the original version:
  * Real file instead of code pasted in a README.
  * Persistent storage (SQLite) - data survives server reloads.
  * Multiple ads with weighted random rotation.
  * Impressions + clicks + CTR, with daily statistics.
  * Admin panel protected by a password (HTTP Basic Auth) + CSRF protection.
  * No template injection (the old f-string + render_template_string was unsafe).
  * Safe uploads: extension whitelist, magic-byte check, size limit, random names.
  * Only http/https URLs are accepted for ads.
  * Simple per-IP rate limit on the public tracking endpoints.
  * Arabic / English admin panel.

Setup on PythonAnywhere: see README.md next to this file.
"""

import hmac
import os
import random
import secrets
import sqlite3
import threading
import time
import uuid
from datetime import date
from urllib.parse import urlparse

from flask import (Flask, Response, abort, g, jsonify, redirect,
                   render_template_string, request, session, url_for)

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("AD_DATA_DIR", os.path.join(BASE_DIR, "data"))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "ads_images")
DB_PATH = os.path.join(DATA_DIR, "ads.db")

# Admin credentials. Prefer environment variables; otherwise edit these two lines.
# The admin panel stays LOCKED until you set a real password.
ADMIN_USER = os.environ.get("AD_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.environ.get("AD_ADMIN_PASSWORD", "")

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
RATE_LIMIT_PER_MIN = 120  # tracking requests per IP per minute

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _load_secret_key():
    """Persistent random secret key, so sessions survive restarts."""
    env_key = os.environ.get("AD_SECRET_KEY")
    if env_key:
        return env_key
    path = os.path.join(DATA_DIR, "secret.key")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    key = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as f:
        f.write(key)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return key


app = Flask(__name__)
app.config["SECRET_KEY"] = _load_secret_key()
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES + 64 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# ----------------------------------------------------------------------------
# Database
# ----------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS ads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL DEFAULT '',
    image_url   TEXT    NOT NULL,
    target_url  TEXT    NOT NULL,
    weight      INTEGER NOT NULL DEFAULT 1,
    active      INTEGER NOT NULL DEFAULT 1,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks      INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS daily_stats (
    ad_id       INTEGER NOT NULL,
    day         TEXT    NOT NULL,
    impressions INTEGER NOT NULL DEFAULT 0,
    clicks      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (ad_id, day)
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.executescript(SCHEMA)
        if db.execute("SELECT COUNT(*) FROM ads").fetchone()[0] == 0:
            db.execute(
                "INSERT INTO ads (title, image_url, target_url) VALUES (?, ?, ?)",
                ("Demo ad", "https://placehold.co/300x80/png?text=Your+Ad+Here",
                 "https://github.com"),
            )


init_db()

# ----------------------------------------------------------------------------
# Helpers: validation, rate limiting, security
# ----------------------------------------------------------------------------


def is_valid_http_url(value):
    try:
        p = urlparse(value)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc) and len(value) <= 2000


def detect_image_type(head):
    """Return an extension if the bytes look like a supported image, else None."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


_hits = {}
_hits_lock = threading.Lock()


def rate_limited():
    """Very small in-memory limiter (per process) for the public endpoints."""
    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?")
    ip = ip.split(",")[0].strip()
    now = time.time()
    with _hits_lock:
        recent = [t for t in _hits.get(ip, []) if now - t < 60]
        if len(recent) >= RATE_LIMIT_PER_MIN:
            _hits[ip] = recent
            return True
        recent.append(now)
        _hits[ip] = recent
        if len(_hits) > 5000:  # keep memory bounded
            for k in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
                _hits.pop(k, None)
    return False


def admin_configured():
    return len(ADMIN_PASSWORD) >= 8 and ADMIN_PASSWORD != "change-me-please"


def require_admin():
    if not admin_configured():
        return Response(render_template_string(LOCKED_TEMPLATE), 403)
    auth = request.authorization
    ok = (
        auth is not None
        and hmac.compare_digest(auth.username or "", ADMIN_USER)
        and hmac.compare_digest(auth.password or "", ADMIN_PASSWORD)
    )
    if not ok:
        return Response("Authentication required", 401,
                        {"WWW-Authenticate": 'Basic realm="Ad Admin"'})
    return None


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def check_csrf():
    sent = request.form.get("csrf", "")
    expected = session.get("csrf", "")
    if not expected or not hmac.compare_digest(sent, expected):
        abort(400, "Invalid CSRF token")


@app.after_request
def security_headers(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    if request.path.startswith("/admin"):
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


def bump(db, ad_id, column):
    """Increment impressions/clicks (total + today). column is a trusted literal."""
    assert column in ("impressions", "clicks")
    cur = db.execute(f"UPDATE ads SET {column} = {column} + 1 WHERE id = ?", (ad_id,))
    if cur.rowcount == 0:
        return False
    db.execute(
        f"INSERT INTO daily_stats (ad_id, day, {column}) VALUES (?, ?, 1) "
        f"ON CONFLICT(ad_id, day) DO UPDATE SET {column} = {column} + 1",
        (ad_id, date.today().isoformat()),
    )
    db.commit()
    return True


# ----------------------------------------------------------------------------
# Public API (used by the game)
# ----------------------------------------------------------------------------


@app.route("/get-ad")
def get_ad():
    """Return one active ad, chosen randomly by weight."""
    rows = get_db().execute(
        "SELECT id, image_url, target_url, weight FROM ads WHERE active = 1").fetchall()
    if not rows:
        return jsonify({"error": "no active ads"}), 404
    ad = random.choices(rows, weights=[max(1, r["weight"]) for r in rows], k=1)[0]
    resp = jsonify({"id": ad["id"], "image_url": ad["image_url"],
                    "target_url": ad["target_url"]})
    resp.headers["Cache-Control"] = "no-store"
    return resp


def _track(column):
    if rate_limited():
        return jsonify({"status": "rate_limited"}), 429
    raw = request.values.get("ad_id", "")
    if not raw.isdigit():
        return jsonify({"status": "error", "error": "ad_id required"}), 400
    if not bump(get_db(), int(raw), column):
        return jsonify({"status": "error", "error": "unknown ad"}), 404
    return jsonify({"status": "success"})


@app.route("/impression", methods=["POST"])
def register_impression():
    return _track("impressions")


@app.route("/click", methods=["POST", "GET"])  # GET kept for old clients
def register_click():
    return _track("clicks")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def home():
    return redirect(url_for("admin_panel"))


# ----------------------------------------------------------------------------
# Admin panel
# ----------------------------------------------------------------------------
TEXT = {
    "en": {
        "dir": "ltr", "title": "Ad Server Control Panel", "other": "العربية",
        "total": "Totals", "imp": "Impressions", "clk": "Clicks", "ctr": "CTR",
        "today": "Today", "new": "Add a new ad", "name": "Title (internal)",
        "target": "Target URL (opened when the player clicks)",
        "image": "Ad image (drag & drop or click)", "drop": "Drop image here or click to browse",
        "imgurl": "...or a direct image URL", "weight": "Weight (higher = shown more)",
        "add": "Add ad", "save": "Save", "on": "Active", "off": "Paused",
        "pause": "Pause", "resume": "Resume", "del": "Delete", "reset": "Reset stats",
        "confirm": "Are you sure?", "none": "No ads yet.", "ads": "Your ads",
        "created": "Created", "err_url": "Invalid URL (must start with http:// or https://).",
        "err_img": "Provide a valid image (png/jpg/gif/webp, max 2MB) or an image URL.",
        "ok": "Done.",
    },
    "ar": {
        "dir": "rtl", "title": "لوحة تحكم سيرفر الإعلانات", "other": "English",
        "total": "الإجمالي", "imp": "مرات الظهور", "clk": "النقرات", "ctr": "نسبة النقر",
        "today": "اليوم", "new": "إضافة إعلان جديد", "name": "العنوان (للاستخدام الداخلي)",
        "target": "الرابط الهدف (يُفتح عند نقر اللاعب)",
        "image": "صورة الإعلان (اسحب وأفلت أو انقر)", "drop": "أفلت الصورة هنا أو انقر للاختيار",
        "imgurl": "...أو رابط مباشر للصورة", "weight": "الوزن (الأعلى = يظهر أكثر)",
        "add": "إضافة الإعلان", "save": "حفظ", "on": "نشط", "off": "متوقف",
        "pause": "إيقاف", "resume": "تشغيل", "del": "حذف", "reset": "تصفير الإحصائيات",
        "confirm": "هل أنت متأكد؟", "none": "لا توجد إعلانات بعد.", "ads": "إعلاناتك",
        "created": "تاريخ الإنشاء", "err_url": "رابط غير صالح (يجب أن يبدأ بـ http:// أو https://).",
        "err_img": "أضف صورة صالحة (png/jpg/gif/webp بحد أقصى 2MB) أو رابط صورة.",
        "ok": "تم.",
    },
}

LOCKED_TEMPLATE = """<!doctype html><meta charset="utf-8"><title>Locked</title>
<body style="font-family:Arial;max-width:560px;margin:60px auto;line-height:1.7">
<h2>🔒 Admin panel is locked</h2>
<p>Set a password (at least 8 characters) before using the panel:</p>
<pre style="background:#eee;padding:10px">AD_ADMIN_PASSWORD=your-strong-password</pre>
<p>On PythonAnywhere: add <code>os.environ["AD_ADMIN_PASSWORD"] = "..."</code>
at the top of your WSGI file, then press <b>Reload</b>.</p>
<p dir="rtl">🔒 لوحة التحكم مقفلة. اضبط كلمة مرور (8 أحرف على الأقل) في المتغير
<code>AD_ADMIN_PASSWORD</code> ثم أعد تحميل التطبيق.</p></body>"""

ADMIN_TEMPLATE = """<!doctype html>
<html lang="{{ lang }}" dir="{{ t.dir }}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ t.title }}</title>
<style>
 body{font-family:Arial,Tahoma,sans-serif;margin:0;background:#f4f4f9;color:#222}
 .wrap{max-width:860px;margin:0 auto;padding:24px}
 header{display:flex;justify-content:space-between;align-items:center}
 h1{font-size:22px;margin:0} a{color:#0b6bcb}
 .card{background:#fff;border-radius:10px;box-shadow:0 2px 8px rgba(0,0,0,.08);padding:20px;margin:16px 0}
 .stats{display:flex;gap:12px;flex-wrap:wrap}
 .stat{flex:1;min-width:120px;background:#eef1f5;border-radius:8px;padding:12px;text-align:center}
 .stat b{display:block;font-size:22px}
 label{display:block;font-weight:bold;margin:12px 0 4px}
 input[type=text],input[type=url],input[type=number]{width:100%;padding:9px;border:1px solid #ccc;border-radius:6px;box-sizing:border-box}
 .drop{border:2px dashed #0b6bcb;border-radius:8px;height:110px;display:flex;align-items:center;justify-content:center;cursor:pointer;background:#f8f9fa;color:#667;text-align:center;background-size:contain;background-repeat:no-repeat;background-position:center}
 .drop.over{border-color:#28a745;background-color:#e8f5e9}
 button{padding:9px 14px;border:0;border-radius:6px;color:#fff;background:#28a745;cursor:pointer;font-weight:bold}
 button.grey{background:#6c757d} button.red{background:#dc3545}
 .ad{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
 .ad img{width:200px;max-height:70px;object-fit:contain;border:1px solid #ddd;border-radius:6px;background:#fafafa}
 .ad .info{flex:1;min-width:200px;overflow-wrap:anywhere;font-size:14px}
 .badge{padding:2px 8px;border-radius:10px;font-size:12px;color:#fff}
 .on{background:#28a745}.off{background:#999}
 .actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}
 .actions form{display:inline}
 .msg{padding:10px;border-radius:6px;margin:12px 0}
 .msg.ok{background:#e6f4ea}.msg.err{background:#fde8e8}
 small{color:#667}
</style></head><body><div class="wrap">
<header><h1>📢 {{ t.title }}</h1><a href="{{ url_for('admin_panel', lang=other_lang) }}">{{ t.other }}</a></header>

{% if msg %}<div class="msg {{ 'ok' if msg_ok else 'err' }}">{{ msg }}</div>{% endif %}

<div class="card"><b>{{ t.total }}</b>
 <div class="stats" style="margin-top:10px">
  <div class="stat"><b>{{ totals.impressions }}</b>{{ t.imp }}</div>
  <div class="stat"><b>{{ totals.clicks }}</b>{{ t.clk }}</div>
  <div class="stat"><b>{{ totals.ctr }}%</b>{{ t.ctr }}</div>
  <div class="stat"><b>{{ today.impressions }} / {{ today.clicks }}</b>{{ t.today }}</div>
 </div></div>

<div class="card"><b>{{ t.new }}</b>
 <form method="post" action="{{ url_for('admin_add', lang=lang) }}" enctype="multipart/form-data">
  <input type="hidden" name="csrf" value="{{ csrf }}">
  <label>{{ t.name }}</label><input type="text" name="title" maxlength="80">
  <label>{{ t.target }}</label><input type="url" name="target_url" required placeholder="https://example.com">
  <label>{{ t.image }}</label>
  <div class="drop" id="drop">{{ t.drop }}</div>
  <input type="file" name="ad_image" id="file" accept="image/*" hidden>
  <label>{{ t.imgurl }}</label><input type="url" name="image_url" id="imgurl" placeholder="https://.../banner.png">
  <label>{{ t.weight }}</label><input type="number" name="weight" min="1" max="100" value="1">
  <p><button type="submit">{{ t.add }}</button></p>
 </form></div>

<div class="card"><b>{{ t.ads }}</b>
 {% if not ads %}<p>{{ t.none }}</p>{% endif %}
 {% for a in ads %}
 <hr style="border:0;border-top:1px solid #eee;margin:16px 0">
 <div class="ad">
  <img src="{{ a.image_url }}" alt="ad" referrerpolicy="no-referrer">
  <div class="info">
   <b>#{{ a.id }} {{ a.title }}</b>
   <span class="badge {{ 'on' if a.active else 'off' }}">{{ t.on if a.active else t.off }}</span><br>
   <a href="{{ a.target_url }}" target="_blank" rel="noopener noreferrer">{{ a.target_url }}</a><br>
   {{ t.imp }}: {{ a.impressions }} · {{ t.clk }}: {{ a.clicks }} · {{ t.ctr }}: {{ a.ctr }}%
   · {{ t.today }}: {{ a.today_imp }}/{{ a.today_clk }} · ×{{ a.weight }}<br>
   <small>{{ t.created }}: {{ a.created_at }}</small>
   <div class="actions">
    <form method="post" action="{{ url_for('admin_toggle', ad_id=a.id, lang=lang) }}">
     <input type="hidden" name="csrf" value="{{ csrf }}">
     <button class="grey">{{ t.pause if a.active else t.resume }}</button></form>
    <form method="post" action="{{ url_for('admin_reset', ad_id=a.id, lang=lang) }}" onsubmit="return confirm('{{ t.confirm }}')">
     <input type="hidden" name="csrf" value="{{ csrf }}"><button class="grey">{{ t.reset }}</button></form>
    <form method="post" action="{{ url_for('admin_delete', ad_id=a.id, lang=lang) }}" onsubmit="return confirm('{{ t.confirm }}')">
     <input type="hidden" name="csrf" value="{{ csrf }}"><button class="red">{{ t.del }}</button></form>
   </div>
  </div>
 </div>
 {% endfor %}
</div></div>
<script>
 const drop=document.getElementById('drop'),file=document.getElementById('file'),url=document.getElementById('imgurl');
 function show(f){const r=new FileReader();r.onload=()=>{drop.textContent='';drop.style.backgroundImage='url('+r.result+')'};r.readAsDataURL(f);url.value=''}
 drop.onclick=()=>file.click();
 file.onchange=()=>file.files.length&&show(file.files[0]);
 drop.ondragover=e=>{e.preventDefault();drop.classList.add('over')};
 ['dragleave','dragend'].forEach(n=>drop.addEventListener(n,()=>drop.classList.remove('over')));
 drop.ondrop=e=>{e.preventDefault();drop.classList.remove('over');if(e.dataTransfer.files.length){file.files=e.dataTransfer.files;show(e.dataTransfer.files[0])}};
</script></body></html>"""


def _lang():
    lang = request.args.get("lang") or session.get("lang") or "ar"
    lang = lang if lang in TEXT else "ar"
    session["lang"] = lang
    return lang


def _ctr(imp, clk):
    return round(100.0 * clk / imp, 2) if imp else 0.0


@app.before_request
def _admin_guard():
    if request.path.startswith("/admin"):
        denied = require_admin()
        if denied is not None:
            return denied
    return None


@app.route("/admin")
def admin_panel():
    lang = _lang()
    t = TEXT[lang]
    db = get_db()
    today_key = date.today().isoformat()
    today_map = {r["ad_id"]: r for r in db.execute(
        "SELECT * FROM daily_stats WHERE day = ?", (today_key,))}
    ads = []
    for r in db.execute("SELECT * FROM ads ORDER BY id DESC"):
        d = dict(r)
        d["ctr"] = _ctr(d["impressions"], d["clicks"])
        td = today_map.get(d["id"])
        d["today_imp"] = td["impressions"] if td else 0
        d["today_clk"] = td["clicks"] if td else 0
        ads.append(d)
    imp = sum(a["impressions"] for a in ads)
    clk = sum(a["clicks"] for a in ads)
    totals = {"impressions": imp, "clicks": clk, "ctr": _ctr(imp, clk)}
    today = {"impressions": sum(a["today_imp"] for a in ads),
             "clicks": sum(a["today_clk"] for a in ads)}
    code = request.args.get("m")
    msg = t.get({"ok": "ok", "url": "err_url", "img": "err_img"}.get(code, ""), "")
    return render_template_string(
        ADMIN_TEMPLATE, t=t, lang=lang, other_lang="en" if lang == "ar" else "ar",
        ads=ads, totals=totals, today=today, csrf=csrf_token(),
        msg=msg, msg_ok=(code == "ok"))


def _back(code):
    return redirect(url_for("admin_panel", m=code, lang=session.get("lang", "ar")))


def _save_upload(file_storage):
    """Validate and store an uploaded image. Returns its public URL or None."""
    if not file_storage or not file_storage.filename:
        return None
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in ALLOWED_EXT:
        return None
    data = file_storage.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        return None
    real_ext = detect_image_type(data[:16])
    if real_ext is None:
        return None
    name = f"{uuid.uuid4().hex}.{real_ext}"  # never trust the client filename
    with open(os.path.join(UPLOAD_DIR, name), "wb") as f:
        f.write(data)
    return f"{request.host_url}static/ads_images/{name}"


@app.route("/admin/add", methods=["POST"])
def admin_add():
    check_csrf()
    target = request.form.get("target_url", "").strip()
    if not is_valid_http_url(target):
        return _back("url")
    image_url = _save_upload(request.files.get("ad_image"))
    if image_url is None:
        image_url = request.form.get("image_url", "").strip()
        if not is_valid_http_url(image_url):
            return _back("img")
    try:
        weight = min(100, max(1, int(request.form.get("weight", "1"))))
    except ValueError:
        weight = 1
    title = request.form.get("title", "").strip()[:80]
    db = get_db()
    db.execute("INSERT INTO ads (title, image_url, target_url, weight) VALUES (?,?,?,?)",
               (title, image_url, target, weight))
    db.commit()
    return _back("ok")


@app.route("/admin/toggle/<int:ad_id>", methods=["POST"])
def admin_toggle(ad_id):
    check_csrf()
    db = get_db()
    db.execute("UPDATE ads SET active = 1 - active WHERE id = ?", (ad_id,))
    db.commit()
    return _back("ok")


@app.route("/admin/reset/<int:ad_id>", methods=["POST"])
def admin_reset(ad_id):
    check_csrf()
    db = get_db()
    db.execute("UPDATE ads SET impressions = 0, clicks = 0 WHERE id = ?", (ad_id,))
    db.execute("DELETE FROM daily_stats WHERE ad_id = ?", (ad_id,))
    db.commit()
    return _back("ok")


@app.route("/admin/delete/<int:ad_id>", methods=["POST"])
def admin_delete(ad_id):
    check_csrf()
    db = get_db()
    row = db.execute("SELECT image_url FROM ads WHERE id = ?", (ad_id,)).fetchone()
    db.execute("DELETE FROM ads WHERE id = ?", (ad_id,))
    db.execute("DELETE FROM daily_stats WHERE ad_id = ?", (ad_id,))
    db.commit()
    # Remove the uploaded file too (only if it lives in our upload folder).
    if row and "/static/ads_images/" in row["image_url"]:
        fname = os.path.basename(urlparse(row["image_url"]).path)
        path = os.path.join(UPLOAD_DIR, fname)
        if os.path.dirname(os.path.abspath(path)) == os.path.abspath(UPLOAD_DIR) and os.path.exists(path):
            os.remove(path)
    return _back("ok")


@app.errorhandler(413)
def too_large(_e):
    return _back("img")


if __name__ == "__main__":
    app.run(debug=False)
