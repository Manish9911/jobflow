import sys, time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

# where is the sponsorship follow-up button, and what's around it?
d = page.evaluate(
    """() => {
      const b = document.getElementById("primaryQuestionnaire--d5a25d10a03b1001f3d7046620860001");
      const r = b.getBoundingClientRect();
      // elements overlapping the region below the button (menu zone)
      const zone = [];
      const els = document.querySelectorAll("li, div, span");
      for (const e of els) {
        const q = e.getBoundingClientRect();
        if (q.width < 100 || q.height < 12) continue;
        const t = (e.innerText || "").trim();
        if (t.length < 3 || t.length > 100) continue;
        if (t.indexOf(String.fromCharCode(10)) !== -1) continue;
        if (q.top >= r.top - 20 && q.top <= r.top + 500 && Math.abs(q.left - r.left) < 400) {
          zone.push({t: t.slice(0, 80), top: Math.round(q.top), left: Math.round(q.left)});
        }
      }
      return {btn: {top: Math.round(r.top), left: Math.round(r.left), txt: (b.innerText||'').trim()}, zone: zone.slice(0, 20)};
    }"""
)
print(json.dumps(d, indent=1))
b.close()
