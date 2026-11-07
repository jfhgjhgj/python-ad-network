# 🚀 استضف سيرفر الإعلانات الخاص بك (مجاناً على PythonAnywhere)

1. أنشئ حساباً مجانياً على [PythonAnywhere](https://www.pythonanywhere.com/).
2. تبويب **Web** ← **Add a new web app** ← **Flask** ← Python 3.10 أو أحدث.
3. تبويب **Files**: ارفع الملف `flask_app.py` من هذا المجلد إلى `mysite/` (استبدل الموجود).
4. **اضبط كلمة مرور الإدارة** (إجباري – وإلا تبقى اللوحة مقفلة).
   افتح ملف WSGI (تبويب Web ← *WSGI configuration file*) وأضف في أعلاه:
   ```python
   import os
   os.environ["AD_ADMIN_PASSWORD"] = "كلمة-مرور-قوية"   # 8 أحرف أو أكثر (يُفضّل إنجليزية)
   # اختياري: os.environ["AD_ADMIN_USER"] = "admin"
   ```
5. اضغط **Reload** ثم افتح `https://yourusername.pythonanywhere.com/admin`.

## نقاط الوصول
| المسار | الاستخدام |
|---|---|
| `GET /get-ad` | يرجع `{id, image_url, target_url}` (إعلان نشط عشوائي حسب الوزن) |
| `POST /impression` مع `ad_id=` | تُسجّله اللعبة عند ظهور الإعلان |
| `POST /click` مع `ad_id=` | تُسجّله اللعبة عند نقرة حقيقية |
| `/admin` | لوحة التحكم (محمية بكلمة مرور) |

## ملاحظات أمنية
حماية CSRF، أسماء عشوائية للصور مع فحص نوع الملف وحد 2MB، روابط http/https فقط،
حد لعدد الطلبات لكل IP، ولا يوجد حقن قوالب. استخدم عنوان HTTPS لموقعك.
البيانات محفوظة في `data/ads.db` (خذ نسخة احتياطية إن كانت الإحصائيات مهمة).

## استخدام العميل في مشروعك
مجلد `client/` يعمل مع أي مكتبة تفتح نافذة (انظر `client/README.md`):
```python
# pygame
from ad_client import GameAd
ad = GameAd("https://yourusername.pythonanywhere.com", x=250, y=500)
ad.start(); ...; ad.handle_event(event); ad.draw(screen)

# turtle  (سطران فقط)
from ad_tk import TurtleAd
ad = TurtleAd(turtle.Screen(), "https://yourusername.pythonanywhere.com", x=0, y=-250)

# tkinter
from ad_tk import TkAd
TkAd(root, "https://yourusername.pythonanywhere.com").pack()

# أي مكتبة أخرى: نافذة إعلان صغيرة مستقلة
from ad_window import launch_ad_window
launch_ad_window("https://yourusername.pythonanywhere.com")
```
