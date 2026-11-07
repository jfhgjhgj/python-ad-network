# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""Run: python -m unittest discover -s tests -v   (needs flask, pygame, requests)"""
import base64, io, os, sys, tempfile, threading, time, unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["AD_DATA_DIR"] = tempfile.mkdtemp()
os.environ["AD_ADMIN_PASSWORD"] = "test-password-123"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ad-server"))
sys.path.insert(0, os.path.join(ROOT, "client"))

import flask_app  # noqa: E402

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
AUTH = {"Authorization": "Basic " + base64.b64encode(b"admin:test-password-123").decode()}


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.c = flask_app.app.test_client()

    def csrf(self):
        self.c.get("/admin", headers=AUTH)
        with self.c.session_transaction() as s:
            return s["csrf"]

    def test_admin_requires_auth(self):
        self.assertEqual(self.c.get("/admin").status_code, 401)

    def test_get_ad_and_tracking(self):
        ad = self.c.get("/get-ad").get_json()
        self.assertIn("id", ad)
        self.assertEqual(self.c.post("/impression", data={"ad_id": ad["id"]}).status_code, 200)
        self.assertEqual(self.c.post("/click", data={"ad_id": ad["id"]}).status_code, 200)
        self.assertEqual(self.c.post("/click", data={"ad_id": 99999}).status_code, 404)
        self.assertEqual(self.c.post("/click").status_code, 400)

    def test_no_template_injection(self):
        t = self.csrf()
        self.c.post("/admin/add", headers=AUTH, data={
            "csrf": t, "title": "{{7*7}}", "target_url": "https://x.com/?a={{7*7}}",
            "image_url": "https://x.com/i.png"})
        html = self.c.get("/admin", headers=AUTH).get_data(as_text=True)
        self.assertIn("{{7*7}}", html)  # shown literally, never evaluated
        self.assertNotIn(" 49 ", html)

    def test_csrf_enforced(self):
        self.assertEqual(self.c.post("/admin/add", headers=AUTH, data={}).status_code, 400)

    def test_rejects_bad_urls_and_files(self):
        t = self.csrf()
        r = self.c.post("/admin/add", headers=AUTH, data={
            "csrf": t, "target_url": "javascript:alert(1)", "image_url": "https://x/i.png"})
        self.assertIn("m=url", r.headers["Location"])
        r = self.c.post("/admin/add", headers=AUTH, data={
            "csrf": t, "target_url": "https://ok.com",
            "ad_image": (io.BytesIO(b"<?php evil ?>"), "shell.png")},
            content_type="multipart/form-data")
        self.assertIn("m=img", r.headers["Location"])

    def test_valid_upload_gets_random_name(self):
        t = self.csrf()
        r = self.c.post("/admin/add", headers=AUTH, data={
            "csrf": t, "target_url": "https://ok.com",
            "ad_image": (io.BytesIO(PNG), "../../evil name.png")},
            content_type="multipart/form-data")
        self.assertIn("m=ok", r.headers["Location"])
        files = os.listdir(flask_app.UPLOAD_DIR)
        self.assertTrue(any(f.endswith(".png") and ".." not in f for f in files))

    def test_toggle_and_delete(self):
        t = self.csrf()
        self.c.post("/admin/add", headers=AUTH, data={
            "csrf": t, "target_url": "https://t.com", "image_url": "https://t.com/a.png"})
        with flask_app.app.app_context():
            ad_id = flask_app.get_db().execute("SELECT MAX(id) FROM ads").fetchone()[0]
        self.assertEqual(self.c.post(f"/admin/toggle/{ad_id}", headers=AUTH, data={"csrf": t}).status_code, 302)
        self.assertEqual(self.c.post(f"/admin/delete/{ad_id}", headers=AUTH, data={"csrf": t}).status_code, 302)


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from werkzeug.serving import make_server
        cls.srv = make_server("127.0.0.1", 0, flask_app.app, threaded=True)
        cls.port = cls.srv.server_port
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        # make the demo ad point to our own tiny PNG
        with flask_app.app.app_context():
            db = flask_app.get_db()
            with open(os.path.join(flask_app.UPLOAD_DIR, "t.png"), "wb") as f:
                f.write(PNG)
            db.execute("UPDATE ads SET image_url=?, active=1",
                       (f"http://127.0.0.1:{cls.port}/static/ads_images/t.png",))
            db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def test_full_flow(self):
        import pygame
        from ad_client import GameAd
        pygame.init()
        screen = pygame.display.set_mode((400, 200))
        ad = GameAd(f"http://127.0.0.1:{self.port}/get-ad", 10, 10, 100, 40, refresh_interval=0)
        ad.start()
        for _ in range(100):
            ad.draw(screen)
            if ad.image is not None:
                break
            time.sleep(0.05)
        self.assertIsNotNone(ad.image)
        self.assertIsNotNone(ad.ad_id)
        time.sleep(0.5)  # let impression post finish
        import unittest.mock as m
        with m.patch("webbrowser.open", return_value=True) as wb:
            self.assertTrue(ad.check_click((20, 20)))
            self.assertFalse(ad.check_click((20, 20)))  # debounced
            self.assertFalse(ad.check_click((300, 150)))  # outside
            wb.assert_called_once()
        time.sleep(0.5)
        with flask_app.app.app_context():
            row = flask_app.get_db().execute(
                "SELECT impressions, clicks FROM ads WHERE id=?", (ad.ad_id,)).fetchone()
        self.assertEqual((row["impressions"], row["clicks"]), (1, 1))

    def test_blocks_non_http_target(self):
        import pygame
        from ad_client import GameAd
        pygame.init(); pygame.display.set_mode((50, 50))
        ad = GameAd("http://127.0.0.1:9", 0, 0, 10, 10)
        from ad_client import Ad
        ad.image = pygame.Surface((10, 10)); ad._current = Ad(1, "file:///etc/passwd", b"")
        self.assertFalse(ad.check_click((5, 5)))


if __name__ == "__main__":
    unittest.main()
