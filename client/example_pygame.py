import sys
import pygame
from ad_client import GameAd

pygame.init()
win = pygame.display.set_mode((800, 600))
SERVER_URL = "https://yourusername.pythonanywhere.com"   # ⚠️ change me

ad = GameAd(SERVER_URL, x=250, y=500, width=300, height=80)
ad.start()
clock = pygame.time.Clock()
while True:
    win.fill((30, 30, 30))
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            ad.stop(); pygame.quit(); sys.exit()
        ad.handle_event(e)
    ad.draw(win)
    pygame.display.update()
    clock.tick(60)
