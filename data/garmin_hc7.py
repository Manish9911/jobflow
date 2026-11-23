import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
el = f.locator("iframe[title='hCaptcha challenge']").first
cf = el.content_frame
print("challenge url:", cf.frame_url()[:90] if cf else None)
if cf:
    time.sleep(3)
    body = cf.locator("body").inner_text(timeout=10000)
    print("BODY:", body[:600].replace(chr(10), " | "))
    btns = cf.locator("button, input[type=submit], [role=button]")
    n = btns.count()
    for i in range(min(n, 10)):
        try:
            print("BTN:", btns.nth(i).inner_text(timeout=2000)[:40] or btns.nth(i).get_attribute("aria-label"))
        except Exception:
            print("BTN: (no text)")
b.close()
