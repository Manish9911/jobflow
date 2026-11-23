import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

out = f.evaluate(r"""() => {
  const els = [...document.querySelectorAll("a, button, input")];
  const b = els.find(x => (x.innerText || x.value || "").trim().toLowerCase() === "add more (professional experience)");
  if (!b) return "not found";
  b.click();
  return "clicked";
}""")
print(out)
time.sleep(2)
rows = f.evaluate("""() => [...document.querySelectorAll("input[name*='rcf3212']")].map(e => ({name: e.name, val: e.value}))""")
print(json.dumps(rows, indent=1))
b.close()
