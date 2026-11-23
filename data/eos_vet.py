import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)
state = page.evaluate("() => { const b = document.getElementById('personalInfoUS--veteranStatus'); return b ? b.innerText.trim() : 'gone'; }")
print("veteran btn:", state)
if state == "Select One":
    page.locator("#personalInfoUS--veteranStatus").click(timeout=8000)
    time.sleep(2)
res = page.evaluate(
    """(t) => {
      const cands = [...document.querySelectorAll("li, div, span")].filter(e => {
        const r = e.getBoundingClientRect();
        const x = (e.innerText||"").trim();
        return r.width > 0 && r.height > 0 && x === t;
      });
      if (!cands.length) return {err: "no-option"};
      cands.sort((a, bb) => (a.getBoundingClientRect().width*a.getBoundingClientRect().height) - (bb.getBoundingClientRect().width*bb.getBoundingClientRect().height));
      const e = cands[0];
      e.scrollIntoView({block: "center"});
      const r = e.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
    }""",
    "I AM NOT A VETERAN",
)
if res.get("err"):
    print("not visible - options now:", page.evaluate(
        """() => [...document.querySelectorAll("li, div, span")].filter(e => e.getBoundingClientRect().width > 100).map(e => (e.innerText||"").trim()).filter(t => t.length > 3 && t.length < 80 && !t.includes(String.fromCharCode(10))).slice(-12)"""
    ))
    b.close()
    raise SystemExit(1)
page.mouse.click(res["x"], res["y"])
time.sleep(1.5)
state = page.evaluate("() => { const b = document.getElementById('personalInfoUS--veteranStatus'); return b ? b.innerText.trim() : 'gone'; }")
print("veteran now:", state)
b.close()
