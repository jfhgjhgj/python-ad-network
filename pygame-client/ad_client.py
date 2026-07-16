import pygame
import requests
import io
import webbrowser
import threading

class GameAd:
    def __init__(self, api_url, width=300, height=80):
        self.api_url = api_url
        self.width = width
        self.height = height
        self.image = None
        self.target_url = ""
        self.rect = None

    def fetch_ad(self, x, y):
        """تنزيل صورة الإعلان والروابط من السيرفر في الخلفية"""
        try:
            response = requests.get(self.api_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                self.target_url = data["target_url"]
                
                # تحميل الصورة وتحويلها لسطح Pygame جاهز للرسم
                img_res = requests.get(data["image_url"], timeout=3)
                image_bytes = io.BytesIO(img_res.content)
                self.image = pygame.image.load(image_bytes)
                self.image = pygame.transform.scale(self.image, (self.width, self.height))
                self.rect = pygame.Rect(x, y, self.width, self.height)
        except Exception as e:
            print("Failed to load ad (Player might be offline):", e)
            self.image = None

    def draw(self, surface):
        """رسم الإعلان أو مستطيل رمادي مؤقت في حال فشل التحميل"""
        if self.image and self.rect:
            surface.blit(self.image, (self.rect.x, self.rect.y))
        elif self.rect:
            pygame.draw.rect(surface, (100, 100, 100), self.rect)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

    def check_click(self, mouse_pos):
        """التحقق مما إذا كان اللاعب قد ضغط على الإعلان لتوجيهه للمتصفح وتسجيل النقرة"""
        if self.rect and self.rect.collidepoint(mouse_pos):
            if self.target_url:
                webbrowser.open(self.target_url)
                threading.Thread(target=self._send_click_to_server, daemon=True).start()

    def _send_click_to_server(self):
        """إرسال طلب خفي للسيرفر لزيادة عداد النقرات"""
        try:
            base_url = self.api_url.rsplit('/', 1)[0]
            click_url = f"{base_url}/click"
            requests.get(click_url, timeout=5)
            print("Click successfully sent to server!")
        except Exception as e:
            print(f"Failed to register click on server: {e}")
