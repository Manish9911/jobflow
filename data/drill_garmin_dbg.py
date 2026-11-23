"""Debug: list pages + frames for the Garmin iCIMS tab."""
import json
import time

import playwright.sync_api as pw

b = pw.sync_playwright().start()
try:
    browser = b.chromium.connect_over_cdp("http://127.0.0.1:9334")
    ctx = browser.contexts[0]
    for p in ctx.pages:
        if "icims" in p.url or "garmin" in p.url:
            print("PAGE:", p.url[:120])
            for ff in p.frames:
                try:
                    title = ff.title()
                    if ff == p.main_frame:
                        blen = -2
                    else:
                        blen = ff.evaluate("document.body ? document.body.innerText.length : -1")
                except Exception as e:
                    title, blen = f"ERR {type(e).__name__}", -99
                print("  FRAME:", (ff.url or '')[:100], "| title:", str(title)[:60], "| bodylen:", blen)
    time.sleep(2)
finally:
    b.stop()
