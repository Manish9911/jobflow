import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

PDF = "C:/Users/badug/jobflow/data/exports/garmin/Manish Badugu Garmin Senior Software Engineer - Mobile iOS.pdf"
loc = f.locator("input[name='PortalProfileFields.Resume_File']")
print("count:", loc.count(), "hidden:", loc.first.is_hidden())
loc.first.set_input_files(PDF)
time.sleep(10)
val = f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_FileName']\"); return e ? e.value : null; }")
print("hidden name now:", val)
# also check the visible resume label text
lab = f.evaluate(r"""() => {
  const el = document.querySelector('[id*="Resume_File"]');
  const area = document.querySelector('.iCIMS_FileUpload') || (el ? el.closest('td') : null);
  return area ? area.innerText.slice(0, 200) : null;
}""")
print("upload area:", lab)
b.close()
