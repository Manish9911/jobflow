import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate("""() => {
  return [...document.querySelectorAll("a, button, input[type=button], input[type=submit]")].map(e => (e.innerText || e.value || "").trim()).filter(t => t && t.length < 60);
}""")
print(json.dumps(out, indent=1))
# count employment groups (rcf3212 occurrences)
n = f.evaluate("() => [...document.querySelectorAll(\"input[name*='rcf3212']\")].length")
print("rcf3212 count:", n)
b.close()
