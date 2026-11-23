import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
el_handle = f.query_selector("iframe[title='hCaptcha challenge']")
cf = el_handle.content_frame()

# clickable puzzle items
out = cf.evaluate(r"""() => {
  const items = [...document.querySelectorAll('li, .challenge-image, [class*=item], .item')].filter(e => e.offsetParent !== null && e.offsetWidth > 20 && e.offsetWidth < 120 && e.offsetHeight > 20);
  return items.slice(0, 20).map(e => ({
    cls: (e.className||'').slice(0,50),
    txt: (e.innerText||'').trim().slice(0,10),
    rect: e.getBoundingClientRect(),
    aria: e.getAttribute('aria-label'),
  }));
}""")
print(json.dumps(out, indent=1))

# screenshot the challenge region
r = el_handle.bounding_box()
print("iframe box:", r)
page.screenshot(path="C:/Users/badug/jobflow/data/evidence/garmin_hcaptcha.png", clip=r)
print("saved screenshot")
b.close()
