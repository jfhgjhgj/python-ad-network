import pygame
import sys
import threading
from ad_client import GameAd

pygame.init()
win = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Awesome Python Game with Ads")

# وضع الرابط التوضيحي (يستبدله المطور برابط سيرفره الخاص)
my_ad = GameAd("https://YOUR_USERNAME.pythonanywhere.com/get-ad", width=300, height=80)

# جلب الإعلان في الخلفية حتى لا تتجمد اللعبة
threading.Thread(target=my_ad.fetch_ad, args=(250, 500), daemon=True).start()

clock = pygame.time.Clock()

while True:
    win.fill((30, 30, 30)) # خلفية داكنة
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            my_ad.check_click(pygame.mouse.get_pos())
            
    my_ad.draw(win)
    
    pygame.display.update()
    clock.tick(60)
