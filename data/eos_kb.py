import sys, time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

btn_id = "primaryQuestionnaire--" + sys.argv[1]
page.evaluate("id => document.getElementById(id).scrollIntoView({block: 'center'})", btn_id)
time.sleep(0.5)
page.locator("#" + btn_id).focus()
time.sleep(0.5)
page.keyboard.press("Enter")
time.sleep(2)
opts = page.evaluate(
    """() => {
      const seen = {};
      const out = [];
      const els = document.querySelectorAll("li, div, span");
      for (const e of els) {
        const r = e.getBoundingClientRect();
        if (r.width < 100 || r.height < 12) continue;
        const t = (e.innerText || "").trim();
        if (t.length < 3 || t.length > 90) continue;
        if (t.indexOf(String.fromCharCode(10)) !== -1) continue;
        if (t.startsWith("Are ") || t.startsWith("Will ") || t.startsWith("What ") || t.startsWith("Have ") || t.startsWith("You ")) continue;
        if (!seen[t]) { seen[t] = 1; out.push(t); }
      }
      return out.slice(-25);
    }"""
)
print("after Enter:", json.dumps(opts, indent=1))
b.close()
