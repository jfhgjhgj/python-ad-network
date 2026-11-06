# Client - works with any library that opens a window

Copy the files you need next to your game. `adcore.py` is always required.

| Your library | Use | Files |
|---|---|---|
| **pygame** | `GameAd` | `adcore.py` + `ad_client.py` |
| **turtle** | `TurtleAd` | `adcore.py` + `ad_tk.py` |
| **tkinter** | `TkAd` (a normal Canvas) | `adcore.py` + `ad_tk.py` |
| **anything else** (arcade, pyglet, raylib, kivy, ursina...) | `launch_ad_window()` - ad in its own small window | `adcore.py` + `ad_tk.py` + `ad_window.py` |
| anything, drawn inside your window | `AdCore` directly (see `example_any_library.py`) | `adcore.py` |

```python
# turtle, 3 lines
from ad_tk import TurtleAd
ad = TurtleAd(turtle.Screen(), "https://yourname.pythonanywhere.com", x=0, y=-250)
```

Notes
- Everything networking-related runs in a background thread; your game never freezes.
- tkinter/turtle: `pip install pillow` is recommended (JPG/WebP + resizing). Without it only PNG/GIF at original size.
- turtle: `x, y` is the **center** of the ad in turtle coordinates. Avoid `screen.clear()`/`reset()` -
  if you must, the ad redraws itself within a fraction of a second.
- Impressions are counted once per displayed ad, clicks only when the browser really opened.
