import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)

out = f.evaluate(r"""() => {
  const inp = document.querySelector("input[name='PersonProfileFields.Login'], input[type='email'], input[name='email']");
  if (!inp) return {found: false, all: [...document.querySelectorAll("input")].map(e => e.name + "|" + e.type).slice(0, 15)};
  inp.focus();
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
  s.call(inp, "badugu.m7@gmail.com");
  inp.dispatchEvent(new Event("input", {bubbles: true}));
  inp.dispatchEvent(new Event("change", {bubbles: true}));
  return {found: true, name: inp.name, val: inp.value};
}""")
print(out)
time.sleep(1)
f.evaluate(r"""() => {
  const btn = document.querySelector("button#enterEmailSubmitButton, button[type='submit']");
  if (btn) btn.click();
}""")
time.sleep(12)
print("URL:", page.url[:120])
for ff in page.frames:
    try:
        txt = ff.evaluate("() => document.body ? document.body.innerText.slice(0, 400) : ''")
        if txt.strip() and "Branding" not in txt:
            print("FRAME:", txt.replace(chr(10), " | ")[:380])
    except Exception:
        pass
b.close()
