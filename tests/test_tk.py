# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""tkinter + turtle adapters. Needs a display (on Linux CI: xvfb-run -a python -m unittest ...)."""
import base64, gc, os, sys, tempfile, threading, time, unittest
from unittest import mock

os.environ.setdefault("AD_DATA_DIR", tempfile.mkdtemp())
os.environ.setdefault("AD_ADMIN_PASSWORD", "test-password-123")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ad-server"))
sys.path.insert(0, os.path.join(ROOT, "client"))

try:
    import tkinter as tk
    _r = tk.Tk(); _r.destroy()
    HAVE_TK = True
except Exception:
    HAVE_TK = False

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


@unittest.skipUnless(HAVE_TK, "no tkinter / display")
class TkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import flask_app
        from werkzeug.serving import make_server
        cls.fa = flask_app
        cls.srv = make_server("127.0.0.1", 0, flask_app.app, threaded=True)
        cls.url = f"http://127.0.0.1:{cls.srv.server_port}"
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        with open(os.path.join(flask_app.UPLOAD_DIR, "tk.png"), "wb") as f:
            f.write(PNG)
        with flask_app.app.app_context():
            db = flask_app.get_db()
            db.execute("UPDATE ads SET image_url=?, active=1", (cls.url + "/static/ads_images/tk.png",))
            db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def _stats(self, ad_id):
        with self.fa.app.app_context():
            r = self.fa.get_db().execute("SELECT impressions, clicks FROM ads WHERE id=?", (ad_id,)).fetchone()
        return r["impressions"], r["clicks"]

    def _pump(self, root, cond, secs=8):
        end = time.time() + secs
        while time.time() < end and not cond():
            root.update(); time.sleep(0.05)
        return cond()

    def test_tkinter_canvas(self):
        from ad_tk import TkAd
        root = tk.Tk()
        ad = TkAd(root, self.url, width=100, height=40, refresh_interval=0)
        ad.pack()
        self.assertTrue(self._pump(root, lambda: ad._ad is not None and "img" in ad._items))
        ad_id = ad._ad.ad_id
        with mock.patch("webbrowser.open", return_value=True) as wb:
            root.update()
            ad.event_generate("<Button-1>", x=50, y=20)
            self._pump(root, lambda: wb.called, 3)
            wb.assert_called_once()
        time.sleep(0.6)
        self.assertEqual(self._stats(ad_id), (1, 1))
        ad.stop(); root.destroy(); del ad, root; gc.collect()

    def test_turtle(self):
        import turtle
        from ad_tk import TurtleAd
        screen = turtle.Screen()
        screen.setup(400, 300)
        ad = TurtleAd(screen, self.url, x=0, y=-100, width=100, height=40, refresh_interval=0)
        root = screen.getcanvas().winfo_toplevel()
        self.assertTrue(self._pump(root, lambda: "img" in ad._items))
        cv = screen.getcanvas()
        x, y = cv.coords(ad._items["img"])
        self.assertEqual((x, y), (0, 100))  # turtle y=-100  ->  canvas y=+100
        t = turtle.Turtle(); t.forward(50)  # drawing must not hide/delete the ad
        root.update()
        self.assertTrue(ad._alive("img"))
        ad.stop(); turtle.bye(); del ad, cv, root, screen, t; gc.collect()


if __name__ == "__main__":
    unittest.main()
