# 🚀 Host Your Own Pygame Ad Server

To use this ad system, you need to set up your own control panel on **PythonAnywhere** (100% Free).

## 🛠️ Step-by-Step Setup

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com/).
2. Go to the **Web** tab and click **Add a new web app**.
3. Choose **Flask** and select **Python 3.10** (or newer).
4. Go to the **Files** tab, open `mysite/flask_app.py`, delete everything, and paste this Flask Server Code:

```python
import os
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# Create a folder to save uploaded images making them accessible to the game
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'ads_images')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# In-memory database for the advertisement and click tracking
ad_database = {
    "image_url": "https://placehold.co/300x80/png?text=Your+Ad+Here",
    "target_url": "https://github.com",
    "clicks": 0
}

@app.route('/')
def home():
    """Redirect automatically to the admin panel when visiting the home page"""
    return redirect(url_for('admin_panel'))

@app.route('/admin', methods=['GET'])
def admin_panel():
    """Control panel to update ads and view click metrics with drag & drop support"""
    html_content = f"""
    <html>
        <head>
            <title>Ad Server Control Panel</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; background-color: #f4f4f9; direction: ltr; }}
                .container {{ background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); display: inline-block; width: 80%; max-width: 500px; text-align: left; }}
                h2 {{ text-align: center; }}
                .stats {{ background-color: #e9ecef; padding: 15px; margin: 15px 0; border-radius: 6px; font-weight: bold; font-size: 18px; color: #333; text-align: center; }}
                input {{ width: 100%; padding: 10px; margin: 8px 0 18px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
                
                .drop-zone {{
                    width: 100%; height: 120px; border: 2px dashed #007bff; border-radius: 6px;
                    display: flex; align-items: center; justify-content: center; flex-direction: column;
                    cursor: pointer; background-color: #f8f9fa; margin: 8px 0 18px 0; transition: background 0.3s, border-color 0.3s;
                }}
                .drop-zone--over {{ border-color: #28a745; background-color: #e8f5e9; }}
                .drop-zone__input {{ display: none; }}
                .drop-zone__prompt {{ color: #6c757d; text-align: center; font-size: 14px; line-height: 1.5; }}
                .drop-zone__thumb {{
                    width: 100%; height: 100%; border-radius: 4px;
                    background-size: contain; background-repeat: no-repeat; background-position: center;
                }}
                
                button {{ width: 100%; padding: 12px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; }}
                button:hover {{ background-color: #218838; }}
                .reset-btn {{ background-color: #dc3545; margin-top: 10px; }}
                .reset-btn:hover {{ background-color: #c82333; }}
                .preview-box {{ text-align: center; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; }}
                .preview-box img {{ max-width: 100%; height: auto; border: 1px solid #ccc; border-radius: 4px; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>📢 Pygame Ad Control Panel</h2>
                <div class="stats">🖱️ Total Ad Clicks: {ad_database['clicks']}</div>
                
                <form action="/admin/update" method="POST" enctype="multipart/form-data">
                    <label><b>Target URL (Opened when player clicks the ad):</b></label>
                    <input type="url" name="target_url" value="{ad_database['target_url']}" required placeholder="https://example.com">
                    
                    <label><b>Ad Image (Drag & drop here or click to browse):</b></label>
                    <div class="drop-zone" id="ad_drop_zone">
                        <span class="drop-zone__prompt">Drag and drop ad image here<br>or click to browse from your device</span>
                        <input type="file" name="ad_image" id="ad_image_input" class="drop-zone__input" accept="image/*">
                    </div>
                    <label><b>Or enter a direct image URL manually (Optional):</b></label>
                    <input type="text" name="image_url" id="image_url_input" value="{ad_database['image_url']}">
                    
                    <button type="submit">Update Ad Now</button>
                </form>
                
                <form action="/admin/reset" method="POST">
                    <button type="submit" class="reset-btn">Reset Click Counter</button>
                </form>
                <div class="preview-box">
                    <b>Currently Active Ad:</b><br>
                    <img src="{ad_database['image_url']}" alt="Active Ad">
                </div>
            </div>
            <script>
                const dropZone = document.getElementById("ad_drop_zone");
                const inputElement = document.getElementById("ad_image_input");
                const urlInput = document.getElementById("image_url_input");
                dropZone.addEventListener("click", () => inputElement.click());
                inputElement.addEventListener("change", () => {{
                    if (inputElement.files.length) {{
                        updateThumbnail(dropZone, inputElement.files[0]);
                        urlInput.value = "";
                    }}
                }});
                dropZone.addEventListener("dragover", (e) => {{
                    e.preventDefault();
                    dropZone.classList.add("drop-zone--over");
                }});
                ["dragleave", "dragend"].forEach((type) => {{
                    dropZone.addEventListener(type, () => {{
                        dropZone.classList.remove("drop-zone--over");
                    }});
                }});
                dropZone.addEventListener("drop", (e) => {{
                    e.preventDefault();
                    if (e.dataTransfer.files.length) {{
                        inputElement.files = e.dataTransfer.files;
                        updateThumbnail(dropZone, e.dataTransfer.files[0]);
                        urlInput.value = "";
                    }}
                    dropZone.classList.remove("drop-zone--over");
                }});
                function updateThumbnail(dropZoneElement, file) {{
                    let prompt = dropZoneElement.querySelector(".drop-zone__prompt");
                    if (prompt) prompt.remove();
                    let thumbnailElement = dropZoneElement.querySelector(".drop-zone__thumb");
                    if (!thumbnailElement) {{
                        thumbnailElement = document.createElement("div");
                        thumbnailElement.classList.add("drop-zone__thumb");
                        dropZoneElement.appendChild(thumbnailElement);
                    }}
                    const reader = new FileReader();
                    reader.readAsDataURL(file);
                    reader.onload = () => {{
                        thumbnailElement.style.backgroundImage = `url('${{reader.result}}')`;
                    }};
                }}
            </script>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/admin/update', methods=['POST'])
def update_ad():
    """Update ad data whether via uploaded file or direct URL"""
    target_url = request.form.get("target_url")
    image_url = request.form.get("image_url")
    
    if 'ad_image' in request.files:
        file = request.files['ad_image']
        if file and file.filename != '':
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            image_url = f"{request.host_url}static/ads_images/{filename}"

    ad_database["target_url"] = target_url
    if image_url:
        ad_database["image_url"] = image_url
        
    return "<h3>Ad updated successfully! <a href='/admin'>Back to Control Panel</a></h3>"

@app.route('/admin/reset', methods=['POST'])
def reset_clicks():
    """Reset click counter"""
    ad_database["clicks"] = 0
    return redirect(url_for('admin_panel'))

@app.route('/get-ad', methods=['GET'])
def get_ad():
    """Direct cloud endpoint called by the game to fetch ad details"""
    return jsonify({
        "image_url": ad_database["image_url"],
        "target_url": ad_database["target_url"]
    })

@app.route('/click', methods=['GET', 'POST'])
def register_click():
    """Endpoint called by the game to notify server of a click event"""
    ad_database["clicks"] += 1
    return jsonify({"status": "success", "total_clicks": ad_database["clicks"]})

if __name__ == '__main__':
    app.run(debug=True)
