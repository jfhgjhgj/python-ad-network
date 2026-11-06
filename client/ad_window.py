"""
ad_window - show the ad in its OWN small window. Works next to ANY library
(arcade, pyglet, raylib, kivy, ursina, ...) because it runs in a separate process,
so it never fights with your game's main loop.

    from ad_window import launch_ad_window
    launch_ad_window("https://yourname.pythonanywhere.com")   # one line, then run your game

The window closes automatically when your program exits. Needs tkinter
(included with most Python installs) and optionally Pillow.
"""

import argparse
import subprocess
import sys
import threading


def launch_ad_window(server_url, width=300, height=80, x=None, y=None,
                     refresh_interval=60, always_on_top=True):
    """Start the ad window in a separate process. Returns the Popen object."""
    cmd = [sys.executable, __file__, server_url, "--width", str(width),
           "--height", str(height), "--refresh", str(refresh_interval)]
    if x is not None and y is not None:
        cmd += ["--x", str(x), "--y", str(y)]
    if always_on_top:
        cmd.append("--top")
    # The child exits when this pipe closes, i.e. when the parent program ends.
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("server_url")
    ap.add_argument("--width", type=int, default=300)
    ap.add_argument("--height", type=int, default=80)
    ap.add_argument("--x", type=int)
    ap.add_argument("--y", type=int)
    ap.add_argument("--refresh", type=int, default=60)
    ap.add_argument("--top", action="store_true")
    a = ap.parse_args()

    import tkinter as tk
    from ad_tk import TkAd

    root = tk.Tk()
    root.title("Ad")
    root.resizable(False, False)
    if a.top:
        root.attributes("-topmost", True)
    ad = TkAd(root, a.server_url, a.width, a.height, a.refresh)
    ad.pack()
    root.update_idletasks()
    x = a.x if a.x is not None else root.winfo_screenwidth() - a.width - 30
    y = a.y if a.y is not None else root.winfo_screenheight() - a.height - 80
    root.geometry(f"+{x}+{y}")

    def watch_parent():  # stdin hits EOF when the parent process dies
        try:
            sys.stdin.buffer.read()
        finally:
            try:
                root.after(0, root.destroy)
            except Exception:
                pass

    if sys.stdin is not None and not sys.stdin.isatty():
        threading.Thread(target=watch_parent, daemon=True).start()
    root.mainloop()


if __name__ == "__main__":
    _main()
