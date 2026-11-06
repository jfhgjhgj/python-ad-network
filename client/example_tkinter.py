import tkinter as tk
from ad_tk import TkAd

SERVER_URL = "https://yourusername.pythonanywhere.com"   # ⚠️ change me

root = tk.Tk()
root.title("Tkinter app with ads")
tk.Label(root, text="My app", font=("Arial", 24)).pack(padx=40, pady=40)
TkAd(root, SERVER_URL, width=300, height=80).pack(side="bottom", pady=10)
root.mainloop()
