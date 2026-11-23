import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)
out = f.evaluate(r"""() => {
  const res = [];
  // ICIMS error patterns
  document.querySelectorAll(".iCIMS_FormError, .iCIMS_FormError_Icon, [class*='Error'], .error, .alert-error, .iCIMS_Required, span[id*='Error'], div[id*='Error']").forEach(e => {
    const t = (e.innerText || "").trim();
    if (t && t.length < 300) res.push({cls: (e.className || '').toString().slice(0, 60), t: t.slice(0, 200)});
  });
  // required-but-empty marked inputs
  const req = [];
  document.querySelectorAll("input, select, textarea").forEach(e => {
    const parent = e.closest("td");
    if (parent && /error/i.test(parent.className || "")) req.push(e.name);
  });
  return {errs: [...new Map(res.map(r => [r.t, r])).values()].slice(0, 25), err_cells: req.slice(0, 20)};
}""")
print(json.dumps(out, indent=1))
b.close()
