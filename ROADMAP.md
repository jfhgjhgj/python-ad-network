# Roadmap / خارطة الطريق

Status: **Alpha**. Legend: 🟢 beginner-friendly · 🟡 medium · 🔴 advanced.
الحالة: ألفا. 🟢 للمبتدئين · 🟡 متوسط · 🔴 متقدم.

## Priority 1 - Trust the numbers / الثقة بالأرقام
- 🔴 **Signed click tokens:** the server issues a short-lived signed token with each ad; `/impression` and `/click` accept only a valid token, once. (Makes forging much harder.)
  توقيع النقرات بتوكن قصير العمر يصدره السيرفر، يُقبل مرة واحدة.
- 🟡 Basic bot filtering (ignore clicks that arrive less than N ms after the ad was served).
- 🟢 Unique-per-IP click counting window (count one click per IP per ad per hour).

## Priority 2 - Ad management / إدارة الإعلانات
- 🟡 Scheduling: start and end dates per ad.
- 🟡 Frequency capping per player (client keeps a small local counter).
- 🟢 Edit an existing ad (title, URL, weight) from the admin panel.
- 🟢 Export stats as CSV.
- 🟡 Ad sizes / placements: serve different ads for different box sizes.
- 🔴 Multiple advertiser accounts with separate dashboards.

## Priority 3 - More libraries / مكتبات أكثر
- 🟡 pyglet adapter · 🟡 arcade adapter · 🟡 Kivy adapter · 🟡 raylib (`pyray`) adapter
- 🟡 Pygame Zero helper
- 🟢 More examples in `client/` (a tiny complete game per library)

## Priority 4 - Quality / الجودة
- 🟡 Test on Windows and macOS, and on the real PythonAnywhere environment (reports welcome as Issues).
- 🟢 Screenshots / GIF of the admin panel and the client in the README.
- 🟢 Translate the admin panel into more languages (strings are in the `TEXT` dict in `flask_app.py`).
- 🟡 Package the client for `pip install` (`pyproject.toml`).
- 🟡 Optional PostgreSQL support for bigger traffic.
- 🟢 GitHub Actions workflow running the tests on every push.

## Out of scope (for now)
Real-time bidding, advertiser billing, ad exchanges. This project is a small core; those belong in projects built on top of it.
خارج النطاق حاليًا: المزادات الفورية والفوترة وتبادل الإعلانات.
