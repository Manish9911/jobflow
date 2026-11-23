import sys, time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

btn_id = "primaryQuestionnaire--" + sys.argv[1]
answer = sys.argv[2]

page.evaluate("() => document.body.click()")
time.sleep(0.4)
page.locator("#" + btn_id).click(timeout=8000)
time.sleep(1.5)
res = page.evaluate(
    """(t) => {
      const cands = [...document.querySelectorAll("li, div, span")].filter(e => {
        const r = e.getBoundingClientRect();
        const x = (e.innerText||"").trim();
        return r.width > 0 && r.height > 0 && x.length > 5 && x.indexOf(t) !== -1;
      });
      if (!cands.length) return {err: "no-option"};
      // pick the deepest (smallest area) match
      cands.sort((a, b) => (a.getBoundingClientRect().width*a.getBoundingClientRect().height) - (b.getBoundingClientRect().width*b.getBoundingClientRect().height));
      const e = cands[0];
      e.scrollIntoView({block: "center"});
      const r = e.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), txt: (e.innerText||"").trim().slice(0,80)};
    }""",
    answer,
)
if res.get("err"):
    print("FAILED: option not found:", answer)
    b.close()
    sys.exit(1)
print("clicking:", res.get("txt"))
page.mouse.click(res["x"], res["y"])
time.sleep(1.5)
state = page.evaluate(
    "id => { const b = document.getElementById(id); return b ? b.innerText.trim() : 'gone'; }",
    btn_id,
)
print("button now shows:", state)
b.close()
