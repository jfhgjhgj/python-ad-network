import turtle
from ad_tk import TurtleAd

SERVER_URL = "https://yourusername.pythonanywhere.com"   # ⚠️ change me

screen = turtle.Screen()
screen.setup(800, 600)
screen.title("Turtle game with ads")

# center of the ad in turtle coordinates (0,0 = middle of the window)
ad = TurtleAd(screen, SERVER_URL, x=0, y=-250, width=300, height=80)

t = turtle.Turtle()
t.pensize(3)
for _ in range(36):
    t.forward(120); t.left(100)

turtle.done()
