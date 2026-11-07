# Contributing / المساهمة

Thanks for helping! This project is an **alpha core** - small, focused contributions are the best.
شكرًا لمساعدتك! المشروع نواة تجريبية، وأفضل المساهمات هي الصغيرة والمحددة.

## Setup
```bash
git clone <your fork>
pip install flask requests pygame pillow
python -m unittest discover -s tests -v          # Windows / macOS / desktop Linux
xvfb-run -a python -m unittest discover -s tests -v   # Linux without a display
```
The tkinter/turtle tests are skipped automatically if no display is available.

## Where things live
| You want to... | Edit |
|---|---|
| Support a new window library | add an adapter on top of `client/adcore.py` (see `ad_client.py`, `ad_tk.py`) |
| Change what the server does | `ad-server/flask_app.py` |
| Fix download / tracking / click logic | `client/adcore.py` |

## Rules
1. **Add or update a test** for any behavior you change.
2. **Keep the tests green** before opening a pull request.
3. **Security first:** never build HTML with f-strings, never trust uploaded filenames, never open non-http(s) links, keep CSRF checks on every admin POST.
4. **License header:** every new `.py` file starts with
   ```python
   # This Source Code Form is subject to the terms of the Mozilla Public
   # License, v. 2.0. If a copy of the MPL was not distributed with this
   # file, You can obtain one at https://mozilla.org/MPL/2.0/.
   # SPDX-License-Identifier: MPL-2.0
   ```
   By contributing you agree your work is released under MPL-2.0.
5. Keep the client dependency-light (`adcore.py` needs only `requests`).
6. One pull request = one idea. Describe what and why.

## Good places to start
See [ROADMAP.md](ROADMAP.md) - items marked 🟢 are beginner-friendly.

## AI-assisted contributions
Allowed, but you are responsible for the code: read it, test it, and understand it. You may credit the tool with a commit trailer, e.g. `Co-authored-by: Claude <noreply@anthropic.com>`.
المساهمات بمساعدة الذكاء الاصطناعي مقبولة، لكنك المسؤول عن فهم الكود واختباره.
