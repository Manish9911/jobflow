import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
f.reload()
time.sleep(12)
# re-fill email
out = f.evaluate(r"""() => {
  const inp = document.querySelector("input[name='css_loginName']");
  if (!inp) return "no input";
  inp.focus();
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  s.call(inp, "badugu.m7@gmail.com");
  inp.dispatchEvent(new Event("input", {bubbles: true}));
  inp.dispatchEvent(new Event("change", {bubbles: true}));
  return "filled";
}""")
print(out)
time.sleep(2)
# find hcaptcha iframe
clicked = "no frame"
for attempt in range(3):
    frames = page.frames
    for ff in frames:
        if "hcaptcha.com" in ff.url:
            print("hc frame:", ff.url[:90])
            try:
                cb = ff.locator("input[type='checkbox']")
                if cb.count():
                    cb.first.click(timeout=8000)
                    clicked = "clicked checkbox"
            except Exception as e:
                clicked = f"err: {str(e)[:80]}"
            break
    if clicked == "clicked checkbox":
        break
    time.sleep(5)
print("clicked:", clicked)
time.sleep(12)
print("URL:", page.url[:120])
for ff in page.frames:
    try:
        txt = ff.evaluate("() => document.body ? document.body.innerText.slice(0, 300) : ''")
        if txt.strip() and 'Branding' not in txt and 'hcaptcha' not in ff.url:
            print("FRAME:", txt.replace(chr(10), " | ")[:280])
    except Exception:
        pass
b.close()
