import pygame
import sys
import threading
from ad_client import GameAd

pygame.init()
win = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Awesome Python Game with Ads")

# ⚠️ Replace 'yourusername' with your actual PythonAnywhere username
SERVER_URL = "https://yourusername.pythonanywhere.com/get-ad"

# Instantiate GameAd specifying position (x=250, y=500) and dimensions
my_ad = GameAd(SERVER_URL, x=250, y=500, width=300, height=80)

# Fetch ad asynchronously to prevent game freezing on startup
threading.Thread(target=my_ad.fetch_ad, daemon=True).start()

clock = pygame.time.Clock()

while True:
    win.fill((30, 30, 30))  # Dark background
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            my_ad.check_click(pygame.mouse.get_pos())
            
    # Render advertisement on screen
    my_ad.draw(win)
    
    pygame.display.update()
    clock.tick(60)
