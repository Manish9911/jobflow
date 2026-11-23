import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
print("TOP URL:", page.url)
for i, ff in enumerate(page.frames):
    print(f"FRAME {i}:", ff.url[:120])
# find the profileButton in each frame
for i, ff in enumerate(page.frames):
    try:
        has = ff.evaluate("() => !!document.querySelector('input[name=profileButton]')")
        if has:
            print(f"  -> profileButton in frame {i}")
    except Exception as e:
        pass
b.close()
