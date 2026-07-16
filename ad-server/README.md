# 🚀 Host Your Own Pygame Ad Server

To use this ad system, you need to set up your own control panel on **PythonAnywhere** (100% Free).

## 🛠️ Step-by-Step Setup

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com/).
2. Go to the **Web** tab and click **Add a new web app**.
3. Choose **Flask** and select **Python 3.10** (or newer).
4. Go to the **Files** tab, open `mysite/flask_app.py`, delete everything, and paste this Flask Server Code:

```python
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

ad_database = {
    "image_url": "[https://placehold.co/300x80/png?text=Your+Ad+Here](https://placehold.co/300x80/png?text=Your+Ad+Here)",
    "target_url": "[https://github.com](https://github.com)",
    "clicks": 0
}

@app.route('/')
def home():
    return redirect(url_for('admin_panel'))

@app.route('/admin', methods=['GET'])
def admin_panel():
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
                <div class="stats">🖱️ Total Ad Clicks: {ad_database['clicks']}</div>
                <form action="/admin/update" method="POST">
                    <label>Ad Image URL (300x80 recommended):</label>
                    <input type="text" name="image_url" value="{ad_database['image_url']}" required>
                    <label>Target Destination URL:</label>
                    <input type="text" name="target_url" value="{ad_database['target_url']}" required>
                    <button type="submit">Update Ad Instantly</button>
                </form>
                <form action="/admin/reset" method="POST">
                    <button type="submit" class="reset-btn">Reset Click Counter</button>
                </form>
            </div>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/admin/update', methods=['POST'])
def update_ad():
    ad_database["image_url"] = request.form.get("image_url")
    ad_database["target_url"] = request.form.get("target_url")
    return "<h3>Ad Updated Successfully! <a href='/admin'>Go Back</a></h3>"

@app.route('/admin/reset', methods=['POST'])
def reset_clicks():
    ad_database["clicks"] = 0
    return redirect(url_for('admin_panel'))

@app.route('/get-ad', methods=['GET'])
def get_ad():
    return jsonify({
        "image_url": ad_database["image_url"],
        "target_url": ad_database["target_url"]
    })

@app.route('/click', methods=['GET', 'POST'])
def register_click():
    ad_database["clicks"] += 1
    return jsonify({"status": "success", "total_clicks": ad_database["clicks"]})

if __name__ == '__main__':
    app.run(debug=True)
