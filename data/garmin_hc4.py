import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

# get the challenge iframe element and its content frame
out = f.evaluate(r"""() => {
  const ifs = [...document.querySelectorAll('iframe')].filter(e => e.title === 'hCaptcha challenge');
  return ifs.map(e => e.getBoundingClientRect());
}""")
print("challenge rects:", out)

el = f.locator("iframe[title='hCaptcha challenge']").first
cf = el.content_frame(timeout=15000)
print("content frame:", cf.url[:100] if cf else None)
if cf:
    time.sleep(3)
    inner = cf.evaluate(r"""() => ({
      body: document.body ? document.body.innerText.slice(0, 400) : 'no body',
      iframes: [...document.querySelectorAll('iframe')].map(e => ({src: (e.src||'').slice(0,80), w: e.offsetWidth, h: e.offsetHeight})),
    })""")
    print(inner)
b.close()
