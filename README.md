# python-ad-network

> 🇸🇦 [النسخة العربية](README_AR.md)

A small, self-hosted **ad network core** for Python games and apps - works with **pygame, turtle, tkinter**, and (through a separate window) **any other library that opens a window**.

> ⚠️ **Status: Alpha.** This is a *core* to build on, not a finished product. It works and is tested on Linux, but expect rough edges and missing features. See [What is missing](#what-is-missing-alpha) and the [ROADMAP](ROADMAP.md). **Do not use it to bill advertisers yet** - click numbers can be forged.

## Why?
Google's ad products do not support desktop Python games (AdMob targets mobile SDKs, AdSense is for websites). If you make small games and want to promote your other games, show a sponsor, or learn how an ad server works, you need something simple that you control. This is that starting point.

## What you get
- **Server** (Flask + SQLite): several ads with weighted rotation, impressions / clicks / CTR, daily stats, an Arabic/English admin panel with drag & drop upload.
- **Client**: non-blocking (background thread), auto-refresh, offline cache, safe link opening (http/https only), impression and click tracking.
- **Adapters**: pygame (`GameAd`), tkinter (`TkAd`), turtle (`TurtleAd`), and `launch_ad_window()` for everything else.
- **Tests**: 11 automated tests (server security, tracking, pygame, tkinter, turtle).

## Quick start

**1. Server** - host it free on PythonAnywhere. Full steps: [ad-server/README.md](ad-server/README.md).
You must set an admin password first (the panel stays locked otherwise):
```python
import os
os.environ["AD_ADMIN_PASSWORD"] = "your-strong-password"   # 8+ characters
```

**2. Client** - copy the files you need from `client/` next to your game (`adcore.py` is always required):
```python
# pygame
from ad_client import GameAd
ad = GameAd("https://yourname.pythonanywhere.com", x=250, y=500, width=300, height=80)
ad.start()                  # before the game loop
ad.handle_event(event)      # inside the loop, for every event
ad.draw(screen)

# turtle
from ad_tk import TurtleAd
TurtleAd(turtle.Screen(), "https://yourname.pythonanywhere.com", x=0, y=-250)

# tkinter
from ad_tk import TkAd
TkAd(root, "https://yourname.pythonanywhere.com").pack()

# any other library: the ad opens in its own small window
from ad_window import launch_ad_window
launch_ad_window("https://yourname.pythonanywhere.com")
```
More in [client/README.md](client/README.md) and the `client/example_*.py` files.

## Project structure
```
ad-server/flask_app.py     the whole server (API + admin panel + database)
client/adcore.py           GUI-independent core: download, refresh, cache, tracking, safe click
client/ad_client.py        pygame adapter        ┐
client/ad_tk.py            tkinter + turtle      ├ thin adapters on top of adcore
client/ad_window.py        separate window       ┘ for any other library
tests/                     automated tests
```
Adding support for a new library = writing a small adapter on top of `AdCore` (see `client/example_any_library.py`). That is the easiest way to contribute.

## What is missing (Alpha)
Be aware before you use it:
- 🔓 **Clicks and impressions can be forged** - anyone who knows the URL can POST fake events. The per-IP rate limit only slows floods down.
- No advertiser accounts, billing, ad review, or targeting. You add ads manually from the admin panel.
- Random weighted selection only (no auction, no frequency capping, no scheduling).
- Tested on **Linux** with Python 3.12 only. Windows / macOS / the real PythonAnywhere environment are untested.
- SQLite on free hosting is fine for small projects, not for high traffic.
- No GDPR/consent tooling - you are responsible for your own legal obligations.

## Contributing
Help is very welcome - this project is meant to be a base others extend. Read [CONTRIBUTING.md](CONTRIBUTING.md) and pick something from the [ROADMAP](ROADMAP.md) (look for `good first issue`).

## License
[Mozilla Public License 2.0 (MPL-2.0)](LICENSE) - file-level copyleft.
- Using this project in your game/app, even a closed-source one, is free. You do **not** have to open your own code.
- If you modify files of this project and distribute them, those modified files must stay open source under MPL-2.0.

*This is a summary, not legal advice.*

## Acknowledgements
Created by the project author, with development assistance from Claude (Anthropic).
