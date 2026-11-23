import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
el_handle = f.query_selector("iframe[title='hCaptcha challenge']")
cf = el_handle.content_frame()
print("challenge url:", cf.url[:90] if cf else None)
if cf:
    time.sleep(3)
    out = cf.evaluate(r"""() => ({
      body: document.body ? document.body.innerText.slice(0, 600) : 'no body',
      btns: [...document.querySelectorAll('button, input[type=submit], [role=button]')].map(e => ({t: (e.innerText || e.value || '').trim().slice(0,40), cls: (e.className||'').slice(0,50)})),
      iframes: [...document.querySelectorAll('iframe')].map(e => ({src: (e.src||'').slice(0,70), w: e.offsetWidth, h: e.offsetHeight})),
    })""")
    print(json.dumps(out, indent=1))
b.close()
