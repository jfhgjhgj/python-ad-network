# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
tkinter + turtle adapters for the Python Ad Network (built on adcore.AdCore).

    # tkinter
    ad = TkAd(root_or_frame, "https://yourname.pythonanywhere.com", width=300, height=80)
    ad.pack(side="bottom")            # it is a normal tk.Canvas

    # turtle  (turtle is tkinter inside, so it draws on the turtle window)
    ad = TurtleAd(turtle.Screen(), "https://yourname.pythonanywhere.com",
                  x=0, y=-250, width=300, height=80)   # x,y = center, turtle coordinates

Pillow (pip install pillow) is recommended: it adds JPG/WebP and resizing.
Without it only PNG/GIF work and they are shown at their original size.
"""

import io
import logging
import tkinter as tk

from adcore import AdCore

try:
    from PIL import Image, ImageTk
except ImportError:  # optional
    Image = ImageTk = None

log = logging.getLogger("gamead")
POLL_MS = 250


def _make_photo(image_bytes, width, height, fit="contain"):
    """bytes -> tk image object (must run on the Tk thread)."""
    if Image is not None:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        if fit == "contain":
            img.thumbnail((width, height), Image.LANCZOS)
        else:
            img = img.resize((width, height), Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    import base64
    return tk.PhotoImage(data=base64.b64encode(image_bytes))  # PNG/GIF only


class _AdMixin:
    """Shared logic: poll the core, show the image on a Canvas, handle clicks."""

    def _init_ad(self, canvas, server_url, width, height, refresh_interval,
               timeout, fit, show_label, cache_dir):
        self.core = AdCore(server_url, refresh_interval, timeout, cache_dir)
        self._cv, self.width, self.height = canvas, width, height
        self.fit, self.show_label = fit, show_label
        self._ad = None
        self._photo = None
        self._items = {}
        self._running = False
        self._after_id = None

    # --- subclasses give the canvas-space center of the ad box
    def _center(self):
        raise NotImplementedError

    def start(self):
        self.core.start()
        if not self._running:
            self._running = True
            self._after_id = self._cv.after(POLL_MS, self._tick)

    def stop(self):
        self._running = False
        self.core.stop()
        if self._after_id is not None:
            try:
                self._cv.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _clear_items(self):
        for key in list(self._items):
            try:
                self._cv.delete(self._items.pop(key))
            except tk.TclError:
                pass

    def _alive(self, key):
        item = self._items.get(key)
        if item is None:
            return False
        try:
            return bool(self._cv.type(item))
        except tk.TclError:
            return False

    def _tick(self):
        if not self._running:
            return
        try:
            new = self.core.take_new()
            if new is not None:
                try:
                    self._photo = _make_photo(new.image_bytes, self.width, self.height, self.fit)
                    self._ad = new
                    self._clear_items()  # redraw with the new image
                except Exception as e:
                    log.warning("Bad ad image: %s", e)
            if self._ad is not None and self._photo is not None:
                self._ensure_items()
                self.core.report_impression(self._ad)
            self._after_id = self._cv.after(POLL_MS, self._tick)
        except tk.TclError:  # window was closed
            self._running = False
            self.core.stop()

    def _ensure_items(self):
        cx, cy = self._center()
        cv = self._cv
        if not self._alive("img"):
            old = self._items.pop("img", None)
            if old:
                try:
                    cv.delete(old)
                except tk.TclError:
                    pass
            item = cv.create_image(cx, cy, image=self._photo, tags="gamead")
            self._items["img"] = item
            cv.tag_bind(item, "<Button-1>", lambda e: self.core.open_ad(self._ad))
            cv.tag_bind(item, "<Enter>", lambda e: cv.config(cursor="hand2"))
            cv.tag_bind(item, "<Leave>", lambda e: cv.config(cursor=""))
        if self.show_label and not self._alive("label"):
            x = cx + self._photo.width() / 2 - 14
            y = cy - self._photo.height() / 2 + 8
            bg = cv.create_rectangle(x - 12, y - 8, x + 12, y + 8, fill="#222", outline="", tags="gamead")
            txt = cv.create_text(x, y, text="Ad", fill="white", font=("Arial", 8), tags="gamead")
            self._items["label"] = txt
            self._items["label_bg"] = bg
        cv.tag_raise("gamead")


class TkAd(tk.Canvas, _AdMixin):
    """A normal tkinter Canvas that shows the ad. Use pack()/grid()/place()."""

    def __init__(self, master, server_url, width=300, height=80, refresh_interval=60,
                 timeout=5, fit="contain", show_label=True, cache_dir=None, autostart=True,
                 **canvas_options):
        canvas_options.setdefault("highlightthickness", 0)
        canvas_options.setdefault("bg", "#646464")
        tk.Canvas.__init__(self, master, width=width, height=height, **canvas_options)
        self._init_ad(self, server_url, width, height, refresh_interval, timeout,
                    fit, show_label, cache_dir)
        if autostart:
            self.start()

    def _center(self):
        return self.width / 2, self.height / 2


class TurtleAd(_AdMixin):
    """Shows the ad inside a turtle window. x, y = center in turtle coordinates."""

    def __init__(self, screen, server_url, x=0, y=0, width=300, height=80,
                 refresh_interval=60, timeout=5, fit="contain", show_label=True,
                 cache_dir=None, autostart=True):
        self._tx, self._ty = x, y
        self.screen = screen
        self._init_ad(screen.getcanvas(), server_url, width, height, refresh_interval,
                    timeout, fit, show_label, cache_dir)
        if autostart:
            self.start()

    def _center(self):
        # turtle's canvas origin is the window center and its y axis points up
        return self._tx, -self._ty

    def move(self, x, y):
        self._tx, self._ty = x, y
        self._clear_items()
