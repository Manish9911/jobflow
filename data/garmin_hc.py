import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
print("all frames:")
for ff in page.frames:
    print("  ", ff.url[:110])
# find the hcaptcha widget frame with a checkbox
done = False
for ff in page.frames:
    if "hcaptcha" in ff.url:
        try:
            cb = ff.locator("input[type=checkbox], #challenge-stage, .h-captcha")
            if cb.count():
                print("candidate frame:", ff.url[:90], "count:", cb.count())
        except Exception as e:
            pass
b.close()
