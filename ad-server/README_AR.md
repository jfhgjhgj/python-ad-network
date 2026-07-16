# 🚀 اصنع سيرفر الإعلانات الخاص بك للعبة Pygame مجاناً!

لكي تتمكن من استخدام مكتبة الإعلانات هذه داخل ألعابك، يجب عليك إنشاء لوحة تحكم وسيرفر خاص بك على منصة **PythonAnywhere** (مجاني 100% ويستغرق 5 دقائق فقط).

هذا النظام يتيح لك التحكم الكامل في تغيير الإعلانات وحساب عدد النقرات سحابياً دون الحاجة لتحديث كود اللعبة أو إيقافها!

---

## 🛠️ دليل الإعداد خطوة بخطوة

### الخطوة 1: إنشاء حساب مجاني
1. توجه إلى موقع [PythonAnywhere](https://www.pythonanywhere.com/).
2. قم بإنشاء حساب مجاني جديد واختيار الخطة المجانية (Beginner Account).

### الخطوة 2: إنشاء تطبيق ويب (Web App)
1. بعد دخولك للوحة التحكم، اذهب إلى تبويب **Web** من القائمة العلوية.
2. اضغط على الزر الأخضر **Add a new web app**.
3. اختر إطار العمل **Flask**، ثم حدد إصدار بايثون **Python 3.10** (أو أحدث إصدار متاح).
4. اترك المسار الافتراضي لملف السيرفر الرئيسي كما هو (غالباً يكون `/home/yourusername/mysite/flask_app.py`) واضغط على **Next**.

### الخطوة 3: كتابة كود السيرفر ولائحة التحكم
1. اذهب إلى تبويب **Files** من القائمة العلوية لحسابك في PythonAnywhere.
2. ادخل إلى مجلد موقعك: `mysite/` ثم افتح ملف **`flask_app.py`**.
3. امسح كل الأسطر الموجودة داخل الملف بالكامل، وألصق كود Flask المطور والآمن التالي:

```python
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# قاعدة البيانات المؤقتة للإعلان وعداد النقرات
ad_database = {
    "image_url": "[https://placehold.co/300x80/png?text=Your+Ad+Here](https://placehold.co/300x80/png?text=Your+Ad+Here)",
    "target_url": "[https://github.com](https://github.com)",
    "clicks": 0
}

@app.route('/')
def home():
    """تحويل تلقائي للوحة التحكم عند زيارة الرابط الرئيسي"""
    return redirect(url_for('admin_panel'))

@app.route('/admin', methods=['GET'])
def admin_panel():
    """لوحة التحكم لتعديل الإعلان وعرض النقرات"""
    html_content = f"""
    <html>
        <head>
            <title>Ad Server Control Panel</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 50px; text-align: center; background-color: #f4f4f9; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; width: 80%; max-width: 500px; }}
                .stats {{ background-color: #e9ecef; padding: 15px; margin: 15px 0; border-radius: 6px; font-weight: bold; font-size: 18px; color: #333; }}
                input {{ width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
                button {{ width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
                button:hover {{ background-color: #218838; }}
                .reset-btn {{ background-color: #dc3545; margin-top: 10px; }}
                .reset-btn:hover {{ background-color: #c82333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📢 Pygame Ad Control Panel</h2>
                <div class="stats">🖱️ إجمالي النقرات على الإعلان: {ad_database['clicks']}</div>
                <form action="/admin/update" method="POST">
                    <label>رابط صورة الإعلان (يفضل أبعاد 300x80):</label>
                    <input type="text" name="image_url" value="{ad_database['image_url']}" required>
                    <label>رابط التوجيه (الموقع الذي يفتحه اللاعب عند الضغط):</label>
                    <input type="text" name="target_url" value="{ad_database['target_url']}" required>
                    <button type="submit">تحديث الإعلان فوراً</button>
                </form>
                <form action="/admin/reset" method="POST">
                    <button type="submit" class="reset-btn">تصفير عداد النقرات</button>
                </form>
            </div>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/admin/update', methods=['POST'])
def update_ad():
    """تحديث بيانات الإعلان"""
    ad_database["image_url"] = request.form.get("image_url")
    ad_database["target_url"] = request.form.get("target_url")
    return "<h3>تم تحديث الإعلان بنجاح! <a href='/admin'>العودة للوحة التحكم</a></h3>"

@app.route('/admin/reset', methods=['POST'])
def reset_clicks():
    """تصفير عداد النقرات"""
    ad_database["clicks"] = 0
    return redirect(url_for('admin_panel'))

@app.route('/get-ad', methods=['GET'])
def get_ad():
    """الرابط السحابي المباشر الذي تستدعيه اللعبة لتنزيل بيانات الإعلان"""
    return jsonify({
        "image_url": ad_database["image_url"],
        "target_url": ad_database["target_url"]
    })

@app.route('/click', methods=['GET', 'POST'])
def register_click():
    """المسار الذي تخبر به اللعبة السيرفر بحدوث نقرة لتحديث العداد"""
    ad_database["clicks"] += 1
    return jsonify({"status": "success", "total_clicks": ad_database["clicks"]})

if __name__ == '__main__':
    app.run(debug=True)
