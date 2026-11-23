import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
el_handle = f.query_selector("iframe[title='hCaptcha challenge']")
cf = el_handle.content_frame()
time.sleep(2)
# click Skip
skip = cf.query_selector(".text:has-text('Skip')")
if skip:
    skip.click()
    print("clicked Skip")
else:
    print("no skip btn")
time.sleep(10)
# check token in parent
wid = f.evaluate("() => document.querySelector('iframe[data-hcaptcha-widget-id]').getAttribute('data-hcaptcha-widget-id')")
token = f.evaluate("() => hcaptcha.getResponse(" + json.dumps(wid) + ")")
print("token:", token[:30] if token else None)
print("URL:", page.url[:110])
body = f.evaluate("() => document.body.innerText.slice(0, 400)")
print("FORM:", body.replace(chr(10), " | ")[:380])
b.close()
