import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
el_handle = f.query_selector("iframe[title='hCaptcha challenge']")
cf = el_handle.content_frame()
time.sleep(2)
out = cf.evaluate(r"""() => {
  const all = [...document.querySelectorAll('*')];
  const vis = all.filter(e => e.offsetParent !== null && e.offsetWidth > 15 && e.offsetHeight > 15 && !e.children.length);
  return vis.map(e => ({
    tag: e.tagName,
    cls: (e.className || '').toString().slice(0, 55),
    txt: (e.textContent || '').trim().slice(0, 8),
    x: Math.round(e.getBoundingClientRect().x),
    y: Math.round(e.getBoundingClientRect().y),
    w: e.offsetWidth,
    h: e.offsetHeight,
  })).slice(0, 40);
}""")
print(json.dumps(out, indent=1))
b.close()
