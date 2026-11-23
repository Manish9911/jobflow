import time, json
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "highroller-careers.com" in p.url)
qs = page.evaluate(
    """() => {
      const out = [];
      const els = [...document.querySelectorAll("label, [class*=question], [class*=field]")];
      const seen = {};
      for (const e of els) {
        const t = (e.innerText||"").trim().replace(/\s+/g, " ");
        if (t.length < 10 || t.length > 220) continue;
        if (!seen[t]) { seen[t] = 1; out.push(t); }
      }
      return out.slice(0, 30);
    }"""
)
for q in qs: print("-", q)
b.close()
