import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

events = []
def on_resp(r):
    if r.request.method == "POST":
        events.append({"url": r.request.url[:130], "status": r.status})
page.on("response", on_resp)
def on_navig(p):
    events.append({"nav": p.url[:130]})
page.on("framenavigated", lambda fr: events.append({"framenav": fr.url[:130]}) if "careers-garmin" in fr.url else None)

btn = f.locator("input[name=profileButton]")
btn.scroll_into_view_if_needed()
print("clicking Update Profile...")
btn.click()
time.sleep(25)
print("TOP URL now:", page.url[:130])
print("EVENTS:")
for e in events[:20]:
    print(" ", e)
# frame state
for ff in page.frames:
    if "careers-garmin" in ff.url:
        try:
            t = ff.evaluate("() => document.body ? document.body.innerText.slice(0, 400) : ''")
            print("FRAME TEXT:", t.replace(chr(10), ' | ')[:400])
        except Exception as ex:
            print("frame err", ex)
b.close()
