import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "in_iframe" not in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)

# any error banners?
errs = f.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll(".iCIMS_FormError, .error, [class*='Error'], [id*='_error'], .alert").forEach(e => {
    const t = (e.innerText || "").trim();
    if (t && t.length < 200) res.push(t);
  });
  return [...new Set(res)].slice(0, 20);
}""")
print("ERRORS:", errs)

# login field state
out = f.evaluate("""() => {
  const g = n => { const e = document.querySelector("input[name='\" + n + \"']"); return e ? e.value.slice(0, 40) : null; };
  return {
    login: g("PersonProfileFields.Login"),
    pw: g("PersonProfileFields.Password"),
    fname: g("PersonProfileFields.FirstName"),
    lname: g("PersonProfileFields.LastName"),
    resume_hidden: g("PortalProfileFields.Resume_FileName"),
    street1: g("316650_PersonProfileFields.AddressStreet1"),
  };
}""")
print(json.dumps(out, indent=1))

# form action + submit buttons
fm = f.evaluate("""() => {
  const form = document.querySelector("form");
  return {action: form ? form.action : null, method: form ? form.method : null};
}""")
print("form:", fm)
btns = f.evaluate("""() => [...document.querySelectorAll("input[type=submit], button")].map(e => ({n: e.name, t: (e.innerText || e.value || "").trim().slice(0, 40)}))""")
print("submits:", btns)
b.close()
