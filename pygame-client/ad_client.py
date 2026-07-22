import pygame
import requests
import io
import webbrowser
import threading

class GameAd:
    def __init__(self, api_url, x=0, y=0, width=300, height=80):
        self.api_url = api_url
        self.width = width
        self.height = height
        self.image = None
        self.target_url = ""
        # Initialize rect immediately to ensure ad region is preserved
        self.rect = pygame.Rect(x, y, self.width, self.height)

    def fetch_ad(self, x=None, y=None):
        """Fetch ad image and target URLs from the server in the background"""
        if x is not None and y is not None:
            self.rect.x = x
            self.rect.y = y

        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.target_url = data["target_url"]
                
                # Fetch and load image
                img_res = requests.get(data["image_url"], timeout=5)
                image_bytes = io.BytesIO(img_res.content)
                
                # Convert and scale image to fit specified dimensions
                loaded_img = pygame.image.load(image_bytes)
                self.image = pygame.transform.scale(loaded_img, (self.width, self.height))
        except Exception as e:
            print("Failed to load ad (Player might be offline or URL is invalid):", e)
            self.image = None

    def draw(self, surface):
        """Draw ad image or fallback rectangle if loading fails or delays"""
        if self.image and self.rect:
            surface.blit(self.image, (self.rect.x, self.rect.y))
        elif self.rect:
            # Draw temporary placeholder box
            pygame.draw.rect(surface, (100, 100, 100), self.rect)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)

    def check_click(self, mouse_pos):
        """Check if player clicked on the ad to open URL in browser and log click"""
        if self.rect and self.rect.collidepoint(mouse_pos):
            if self.target_url:
                webbrowser.open(self.target_url)
                threading.Thread(target=self._send_click_to_server, daemon=True).start()

    def _send_click_to_server(self):
        """Send background request to server to increment click count"""
        try:
            base_url = self.api_url.rsplit('/', 1)[0]
            click_url = f"{base_url}/click"
            requests.get(click_url, timeout=5)
            print("Click successfully sent to server!")
        except Exception as e:
            print(f"Failed to register click on server: {e}")
