# 🚀 Host your own ad server (free on PythonAnywhere)

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com/).
2. **Web** tab → **Add a new web app** → **Flask** → Python 3.10+.
3. **Files** tab: upload `flask_app.py` from this folder to `mysite/` (replace the existing one).
4. **Set the admin password** (required – the panel stays locked otherwise).
   Open the WSGI file (Web tab → *WSGI configuration file*) and add at the very top:
   ```python
   import os
   os.environ["AD_ADMIN_PASSWORD"] = "your-strong-password"   # 8+ characters
   # optional: os.environ["AD_ADMIN_USER"] = "admin"
   ```
5. Press **Reload**, then open `https://yourusername.pythonanywhere.com/admin`.

## Endpoints
| Endpoint | Use |
|---|---|
| `GET /get-ad` | returns `{id, image_url, target_url}` (weighted random active ad) |
| `POST /impression` `ad_id=` | counted by the client when an ad is shown |
| `POST /click` `ad_id=` | counted by the client on a real click |
| `/admin` | control panel (password protected) |

## Security notes
CSRF protection, random upload names + magic-byte check + 2 MB limit, only http/https URLs,
per-IP rate limit on tracking, no template injection. Use the HTTPS address of your site.
Data lives in `data/ads.db` (back it up if you care about the stats).
