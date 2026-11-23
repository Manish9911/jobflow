import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate("""() => {
  const g = n => { const e = document.querySelector("input[name='" + n + "'], select[name='" + n + "']"); return e ? e.value : null; };
  return {
    street1: g("316650_PersonProfileFields.AddressStreet1"),
    city: g("316650_PersonProfileFields.AddressCity"),
    zip: g("316650_PersonProfileFields.AddressZip"),
    state: g("316650_PersonProfileFields.AddressState"),
    country: g("316650_PersonProfileFields.AddressCountry"),
    edu_state: g("491964_CandProfileFields.EducationState"),
    board: g("rcf3049"),
    board_text: g("rcf3049_Text"),
    phone: g("333090_PersonProfileFields.PhoneNumber"),
    employer: g("5397892_PersonProfileFields.rcf3212"),
    emp_city: g("5397892_PersonProfileFields.rcf3216"),
  };
}""")
print(json.dumps(out, indent=1))
b.close()
