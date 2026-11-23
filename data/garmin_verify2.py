import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate(r"""() => {
  const g = n => { const e = document.querySelector("input[name$='." + n + "'], textarea[name$='." + n + "'], select[name$='." + n + "']"); return e ? e.value : null; };
  const sel_txt = n => { const e = document.querySelector("select[name$='." + n + "']"); return e && e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : null; };
  const edu = {
    school: g("CandProfileFields.School"),
    degree: sel_txt("CandProfileFields.Degree"),
    major: g("CandProfileFields.Major") || sel_txt("CandProfileFields.Major"),
    country: sel_txt("CandProfileFields.EducationCountry"),
    state: sel_txt("CandProfileFields.EducationState"),
    startYear: g("CandProfileFields.YearStart"),
    endYear: g("CandProfileFields.YearEnd"),
  };
  const files = document.querySelector("input[name='PortalProfileFields.Resume_File']");
  return {
    edu: edu,
    resume_file: files && files.files ? files.files[0].name : "EMPTY",
    street1: g("AddressStreet1"),
    city: g("AddressCity"),
    zip: g("AddressZip"),
    state: sel_txt("AddressState"),
    phone: g("PersonProfileFields.PhoneNumber"),
    v_z: [g("PersonProfileFields.rcf3212")],
  };
}""")
print(json.dumps(out, indent=1))
b.close()
