import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate(r"""() => {
  // find all inputs whose nearby label says Employer
  const res = [];
  document.querySelectorAll("label").forEach(l => {
    const t = (l.innerText || "").trim();
    if (/^employer$/i.test(t)) {
      let p = l.parentElement;
      for (let i = 0; i < 4 && p; i++) {
        const inp = p.querySelector("input");
        if (inp && inp.type !== "hidden") { res.push({label: t, name: inp.name, val: inp.value}); break; }
        p = p.parentElement;
      }
    }
  });
  return res;
}""")
print(json.dumps(out, indent=1))
b.close()
