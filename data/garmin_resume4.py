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

out = f.evaluate("""() => {
  const inp = document.getElementById('PortalProfileFields.Resume_File');
  const fname = inp.files && inp.files[0] ? inp.files[0].name : 'resume.pdf';
  icims_setFileFieldValue('PortalProfileFields.Resume', fname, '', '', false, 'local');
  return 'called with ' + fname;
}""")
print(out)
time.sleep(8)
val = f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_FileName']\"); return e ? e.value : null; }")
print("hidden name:", val)
print("requests:", reqs)
lab = f.evaluate(r"""() => {
  const e = document.querySelector("input[name='PortalProfileFields.Resume_File']");
  const td = e.closest("td");
  return td ? td.innerText.slice(0, 300) : null;
}""")
print("td text:", lab)
b.close()
