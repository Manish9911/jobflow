import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

# check what's currently set in the file input
cur = f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_File']\"); return e && e.files ? e.files.length + ':' + e.files[0].name : 'no files'; }")
print("file input state:", cur)

PDF = "C:/Users/badug/jobflow/data/exports/garmin/Manish Badugu Garmin Senior Software Engineer - Mobile iOS.pdf"
reqs = []
def on_req(r):
    if r.method in ("POST", "PUT"):
        reqs.append(r.url[:120])
page.on("request", on_req)

loc = f.locator("input[name='PortalProfileFields.Resume_File']")
loc.first.set_input_files(PDF)
time.sleep(3)
cur = f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_File']\"); return e && e.files ? e.files.length + ':' + e.files[0].name : 'no files'; }")
print("after set:", cur)
time.sleep(15)
print("requests:", reqs)
val = f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_FileName']\"); return e ? e.value : null; }")
print("hidden name:", val)
b.close()
