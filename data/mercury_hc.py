import json, time, base64
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-mercuryinsurance" in p.url and "/login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

# capture image responses from hcaptcha
imgs = []
def on_resp(r):
    ct = r.headers.get("content-type", "")
    if "image" in ct and "hcaptcha" in r.url:
        try:
            body = r.body()
            imgs.append({"url": r.url[:150], "ct": ct, "data": body})
        except Exception:
            pass
page.on("response", on_resp)

# fill email
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
print("email:", out)
time.sleep(2)

# trigger fresh captcha
wid = f.evaluate("() => document.querySelector('iframe[data-hcaptcha-widget-id]') ? document.querySelector('iframe[data-hcaptcha-widget-id]').getAttribute('data-hcaptcha-widget-id') : null")
print("widget:", wid)
if wid:
    f.evaluate("() => { try { hcaptcha.reset(" + json.dumps(wid) + "); } catch(e) {} }")
    time.sleep(1.5)
    f.evaluate("() => { try { hcaptcha.execute(" + json.dumps(wid) + "); } catch(e) {} }")

token = None
for i in range(10):
    time.sleep(3)
    token = f.evaluate("() => { try { return hcaptcha.getResponse(" + json.dumps(wid) + "); } catch(e) { return null; } }")
    if token:
        break
print("token:", token[:25] if token else None)
print("images captured:", len(imgs))
for i, im in enumerate(imgs):
    p = f"C:/Users/badug/jobflow/data/evidence/hc_img_{i}.png"
    open(p, "wb").write(im["data"])
    print("saved:", p, im["ct"], len(im["data"]))
b.close()
