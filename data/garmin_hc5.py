import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

wid = f.evaluate("() => document.querySelector('iframe[data-hcaptcha-widget-id]').getAttribute('data-hcaptcha-widget-id')")
print("widget:", wid)
# reset then execute
f.evaluate("() => { try { hcaptcha.reset(" + json.dumps(wid) + "); } catch(e) {} }")
time.sleep(1)
f.evaluate("() => { hcaptcha.execute(" + json.dumps(wid) + "); }")
token = None
for i in range(10):
    time.sleep(3)
    token = f.evaluate("() => hcaptcha.getResponse(" + json.dumps(wid) + ")")
    if token:
        print(f"token after {(i+1)*3}s: {token[:25]}...")
        break
if not token:
    print("no token yet")
    # check if a visible challenge appeared
    ch = f.evaluate(r"""() => {
      const ifs = [...document.querySelectorAll('iframe')].filter(e => (e.title||'').includes('challenge'));
      return ifs.map(e => ({w: e.offsetWidth, h: e.offsetHeight, y: e.getBoundingClientRect().y}));
    }""")
    print("challenge iframes:", ch)
b.close()
