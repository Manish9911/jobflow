import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

reqs = []
def on_req(r):
    if r.method in ("POST", "PUT") or "pload" in r.url:
        reqs.append(r.method + " " + r.url[:130])
page.on("request", on_req)

out = f.evaluate(r"""() => {
  const e = document.querySelector("input[name='PortalProfileFields.Resume_File']");
  e.dispatchEvent(new Event("input", {bubbles: true}));
  e.dispatchEvent(new Event("change", {bubbles: true}));
  return "dispatched";
}""")
print(out)
time.sleep(12)
print("requests:", reqs)
val = f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_FileName']\"); return e ? e.value : null; }")
print("hidden name:", val)
# dump the resume td html to see widget state
html = f.evaluate(r"""() => {
  const e = document.querySelector("input[name='PortalProfileFields.Resume_File']");
  const td = e.closest("td") || e.parentElement.parentElement;
  return td ? td.innerHTML.slice(0, 1500) : "no td";
}""")
print(html)
b.close()
