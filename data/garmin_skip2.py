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
  const skip = [...document.querySelectorAll('*')].find(e => e.children.length === 0 && (e.innerText||'').trim() === 'Skip');
  if (!skip) return "no skip";
  let el = skip;
  for (let i = 0; i < 4 && el.parentElement; i++) {
    el = el.parentElement;
    if (el.tagName === 'BUTTON' || el.className.includes('button')) break;
  }
  ['mousedown', 'mouseup', 'click'].forEach(t => el.dispatchEvent(new MouseEvent(t, {bubbles: true, cancelable: true, view: window})));
  return 'clicked: ' + el.tagName + '.' + el.className.toString().slice(0, 40);
}""")
print(out)
time.sleep(12)
wid = f.evaluate("() => document.querySelector('iframe[data-hcaptcha-widget-id]').getAttribute('data-hcaptcha-widget-id')")
token = f.evaluate("() => hcaptcha.getResponse(" + json.dumps(wid) + ")")
print("token:", token[:30] if token else None)
print("URL:", page.url[:110])
b.close()
