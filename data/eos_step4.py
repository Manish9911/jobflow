import sys, time, json
import playwright.sync_api as pw

JS_OPTS = r"""
() => {
  const seen = {};
  const out = [];
  const els = document.querySelectorAll("li, div, span");
  for (const e of els) {
    const r = e.getBoundingClientRect();
    if (r.width < 50 || r.height < 10) continue;
    const t = (e.innerText || "").trim();
    if (t.length < 15 || t.length > 160) continue;
    if (t.indexOf(String.fromCharCode(10)) !== -1) continue;
    if (!seen[t]) { seen[t] = 1; out.push(t); }
  }
  return out;
}
"""

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

target = sys.argv[1] if len(sys.argv) > 1 else "d5a25d10a03b1001f3d703cb1f500000"

btn_sel = "#primaryQuestionnaire--" + target
state = page.evaluate(
    "id => { const b = document.getElementById(id); return b ? b.innerText.trim() : 'gone'; }",
    "primaryQuestionnaire--" + target,
)
print("btn state:", state)
if state == "Select One":
    page.locator(btn_sel).click(timeout=8000)
    time.sleep(2)
opts = page.evaluate(JS_OPTS)
print(json.dumps(opts, indent=1))
b.close()
