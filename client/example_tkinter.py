# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

import tkinter as tk
from ad_tk import TkAd

SERVER_URL = "https://yourusername.pythonanywhere.com"   # ⚠️ change me

root = tk.Tk()
root.title("Tkinter app with ads")
tk.Label(root, text="My app", font=("Arial", 24)).pack(padx=40, pady=40)
TkAd(root, SERVER_URL, width=300, height=80).pack(side="bottom", pady=10)
root.mainloop()
