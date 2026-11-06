"""
adcore - GUI-independent core of the Python Ad Network client.

It knows nothing about pygame / tkinter / turtle. It only:
  * downloads an ad (JSON + image bytes) in a background thread,
  * refreshes it, caches it for offline use,
  * reports impressions and clicks,
  * opens the target link safely (http/https only, debounced).

Any window library can use it:  see ad_client.py (pygame), ad_tk.py (tkinter and
turtle), ad_window.py (separate window for ANY other library).

    core = AdCore("https://yourname.pythonanywhere.com")
    core.start()
    ad = core.take_new()      # call every frame/tick -> new Ad or None
    ...draw ad.image_bytes with your library...
    core.report_impression(ad)
    core.open_ad(ad)          # when the player clicks
"""

import json
import logging
import os
import threading
import time
import webbrowser
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

log = logging.getLogger("gamead")
MAX_IMAGE_BYTES = 3 * 1024 * 1024


def is_http_url(url):
    try:
        p = urlparse(url)
    except (ValueError, AttributeError):
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


@dataclass
class Ad:
    ad_id: object
    target_url: str
    image_bytes: bytes
    impression_sent: bool = False


class AdCore:
    def __init__(self, server_url, refresh_interval=60, timeout=5, cache_dir=None):
        base = server_url.rstrip("/")
        if base.endswith("/get-ad"):
            base = base[: -len("/get-ad")]
        self.base_url = base
        self.api_url = base + "/get-ad"
        self.refresh_interval = refresh_interval
        self.timeout = timeout
        self.cache_dir = cache_dir
        self._session = requests.Session()
        self._lock = threading.Lock()
        self._pending = None
        self._stop = threading.Event()
        self._thread = None
        self._last_click = 0.0

    # ---------------------------------------------------------------- download
    def _download_image(self, url):
        with self._session.get(url, timeout=self.timeout, stream=True) as r:
            r.raise_for_status()
            if int(r.headers.get("Content-Length") or 0) > MAX_IMAGE_BYTES:
                raise ValueError("ad image too large")
            data = bytearray()
            for chunk in r.iter_content(64 * 1024):
                data += chunk
                if len(data) > MAX_IMAGE_BYTES:
                    raise ValueError("ad image too large")
            return bytes(data)

    def _cache_paths(self):
        return (os.path.join(self.cache_dir, "ad.json"),
                os.path.join(self.cache_dir, "ad.img"))

    def _save_cache(self, ad):
        if not self.cache_dir:
            return
        try:
            os.makedirs(self.cache_dir, exist_ok=True)
            meta, img = self._cache_paths()
            with open(img, "wb") as f:
                f.write(ad.image_bytes)
            with open(meta, "w", encoding="utf-8") as f:
                json.dump({"id": ad.ad_id, "target_url": ad.target_url}, f)
        except OSError as e:
            log.debug("cache write failed: %s", e)

    def _load_cache(self):
        if not self.cache_dir:
            return None
        try:
            meta, img = self._cache_paths()
            with open(meta, encoding="utf-8") as f:
                m = json.load(f)
            with open(img, "rb") as f:
                return Ad(m.get("id"), m.get("target_url", ""), f.read())
        except (OSError, ValueError):
            return None

    def fetch(self):
        """Blocking fetch. Returns True if a new ad is waiting for take_new()."""
        try:
            r = self._session.get(self.api_url, timeout=self.timeout)
            r.raise_for_status()
            d = r.json()
            if not is_http_url(d["target_url"]) or not is_http_url(d["image_url"]):
                raise ValueError("server returned a non-http(s) URL")
            ad = Ad(d.get("id"), d["target_url"], self._download_image(d["image_url"]))
            self._save_cache(ad)
        except Exception as e:
            log.warning("Failed to load ad: %s", e)
            ad = self._load_cache()
            if ad is None:
                return False
        with self._lock:
            self._pending = ad
        return True

    def start(self):
        """Fetch now and keep refreshing in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()

        def loop():
            while not self._stop.is_set():
                self.fetch()
                if self.refresh_interval <= 0:
                    break
                self._stop.wait(self.refresh_interval)

        self._thread = threading.Thread(target=loop, daemon=True, name="gamead")
        self._thread.start()

    def stop(self):
        self._stop.set()

    def take_new(self):
        """Thread-safe: returns a freshly downloaded Ad once, then None."""
        with self._lock:
            ad, self._pending = self._pending, None
        return ad

    # ---------------------------------------------------------------- tracking
    def _post(self, path, ad_id):
        def run():
            try:
                self._session.post(f"{self.base_url}/{path}", data={"ad_id": ad_id},
                                   timeout=self.timeout)
            except requests.RequestException as e:
                log.debug("tracking failed: %s", e)
        threading.Thread(target=run, daemon=True).start()

    def report_impression(self, ad):
        """Call when the ad becomes visible. Counts once per Ad object."""
        if ad is None or ad.impression_sent or ad.ad_id is None:
            return
        ad.impression_sent = True
        self._post("impression", ad.ad_id)

    def open_ad(self, ad):
        """Open the ad link (http/https only) and count the click. Debounced."""
        if ad is None or not is_http_url(ad.target_url):
            return False
        now = time.monotonic()
        if now - self._last_click < 1.0:
            return False
        self._last_click = now
        try:
            opened = webbrowser.open(ad.target_url)
        except Exception as e:
            log.warning("Could not open browser: %s", e)
            opened = False
        if opened and ad.ad_id is not None:
            self._post("click", ad.ad_id)
        return bool(opened)
