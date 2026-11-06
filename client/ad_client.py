"""
Pygame adapter for the Python Ad Network (built on adcore.AdCore).

Backwards compatible with the original API:
    GameAd(".../get-ad"), fetch_ad(), draw(), check_click()
New: start()/stop(), handle_event(), auto refresh, impressions, hover cursor.
"""

import io
import logging

import pygame

from adcore import AdCore, Ad, is_http_url  # noqa: F401  (re-exported)


class GameAd:
    def __init__(self, server_url, x=0, y=0, width=300, height=80,
                 refresh_interval=60, timeout=5, fit="stretch",
                 show_label=True, cache_dir=None):
        """fit: "stretch" fills the box, "contain" keeps the aspect ratio."""
        self.core = AdCore(server_url, refresh_interval, timeout, cache_dir)
        self.base_url, self.api_url = self.core.base_url, self.core.api_url
        self.width, self.height = width, height
        self.rect = pygame.Rect(x, y, width, height)
        self.fit, self.show_label = fit, show_label
        self.image = None
        self._current = None
        self._font = None
        self._hand = False

    # info about the ad currently shown
    @property
    def ad_id(self):
        return self._current.ad_id if self._current else None

    @property
    def target_url(self):
        return self._current.target_url if self._current else ""

    # ------------------------------------------------------------ networking
    def fetch_ad(self, x=None, y=None):
        """Blocking fetch (original API). Use start() for the background version."""
        if x is not None and y is not None:
            self.rect.x, self.rect.y = x, y
        return self.core.fetch()

    def start(self):
        self.core.start()

    def stop(self):
        self.core.stop()

    # ----------------------------------------------------------- main thread
    def _apply(self, ad):
        try:
            surf = pygame.image.load(io.BytesIO(ad.image_bytes))
            if pygame.display.get_surface():
                surf = surf.convert_alpha()
            if self.fit == "contain":
                w, h = surf.get_size()
                k = min(self.width / w, self.height / h)
                size = (max(1, int(w * k)), max(1, int(h * k)))
            else:
                size = (self.width, self.height)
            self.image = pygame.transform.smoothscale(surf, size)
            self._current = ad
        except Exception as e:
            logging.getLogger("gamead").warning("Bad ad image: %s", e)

    def update(self):
        """Call once per frame (draw() does it for you)."""
        ad = self.core.take_new()
        if ad is not None:
            self._apply(ad)
        if self._current is not None and self.image is not None:
            self.core.report_impression(self._current)
            over = self.rect.collidepoint(pygame.mouse.get_pos())
            if over != self._hand:
                self._hand = over
                try:
                    pygame.mouse.set_cursor(
                        pygame.SYSTEM_CURSOR_HAND if over else pygame.SYSTEM_CURSOR_ARROW)
                except pygame.error:
                    pass

    def draw(self, surface):
        self.update()
        if self.image is None:
            pygame.draw.rect(surface, (100, 100, 100), self.rect)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
            return
        ox = (self.width - self.image.get_width()) // 2
        oy = (self.height - self.image.get_height()) // 2
        surface.blit(self.image, (self.rect.x + ox, self.rect.y + oy))
        if self.show_label:
            self._draw_label(surface)

    def _draw_label(self, surface):
        try:
            if self._font is None:
                if not pygame.font.get_init():
                    pygame.font.init()
                self._font = pygame.font.Font(None, 16)
            tag = self._font.render("Ad", True, (255, 255, 255))
            bg = pygame.Rect(self.rect.right - tag.get_width() - 8, self.rect.y,
                             tag.get_width() + 8, tag.get_height() + 2)
            shade = pygame.Surface(bg.size, pygame.SRCALPHA)
            shade.fill((0, 0, 0, 140))
            surface.blit(shade, bg.topleft)
            surface.blit(tag, (bg.x + 4, bg.y + 1))
        except pygame.error:
            pass

    # ---------------------------------------------------------------- clicks
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", 1) == 1:
            return self.check_click(event.pos)
        return False

    def check_click(self, mouse_pos):
        if self.image is None or not self.rect.collidepoint(mouse_pos):
            return False
        return self.core.open_ad(self._current)
