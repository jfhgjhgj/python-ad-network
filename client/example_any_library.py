# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# SPDX-License-Identifier: MPL-2.0

"""
Any other window library (arcade, pyglet, raylib, kivy, ursina, ...).

Option A - easiest: show the ad in its own small window (no code in your game):
"""
from ad_window import launch_ad_window

SERVER_URL = "https://yourusername.pythonanywhere.com"   # ⚠️ change me
launch_ad_window(SERVER_URL, width=300, height=80)       # bottom-right of the screen

# ...now start your game / app as usual...

"""
Option B - draw the ad inside YOUR window using the GUI-independent core:

    from adcore import AdCore
    core = AdCore(SERVER_URL); core.start()

    # every frame / tick:
    ad = core.take_new()               # new Ad (or None)
    if ad:
        my_image = load_with_your_library(ad.image_bytes)   # PNG/JPG/GIF/WebP bytes
    ...draw my_image...
    core.report_impression(current_ad) # when it is visible (counted once per ad)

    # when the player clicks on the ad's area:
    core.open_ad(current_ad)           # opens the link safely + counts the click
"""
