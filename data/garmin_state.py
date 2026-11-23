import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)
out = f.evaluate("""() => {
  const g = n => { const e = document.querySelector("input[name='\" + n + \"'], textarea[name='\" + n + \"'], select[name='\" + n + \"']"); return e ? e.value : null; };
  const gf = id => { const e = document.getElementById(id); return e ? e.value : null; };
  return {
    login: g("PersonProfileFields.Login"),
    fname: g("PersonProfileFields.FirstName"),
    lname: g("PersonProfileFields.LastName"),
    resume_hidden: g("PortalProfileFields.Resume_FileName"),
    phone: g("PersonProfileFields.PhoneNumber"),
    street1: g("316650_PersonProfileFields.AddressStreet1"),
    city: g("316650_PersonProfileFields.AddressCity"),
    zip: g("316650_PersonProfileFields.AddressZip"),
    // work history rows (find any rcf3212)
    emp_rows: [...document.querySelectorAll("input[name$='rcf3212']")].map(e => e.value),
    emp_titles: [...document.querySelectorAll("input[name$='rcf3213']")].map(e => e.value),
    edu_school: [...document.querySelectorAll("input[name$='rcf10013']")].map(e => e.value),
  };
}""")
print(json.dumps(out, indent=1))
b.close()
