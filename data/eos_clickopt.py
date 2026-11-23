import sys, time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

answer = sys.argv[1]
btn_id = sys.argv[2] if len(sys.argv) > 2 else "primaryQuestionnaire--d5a25d10a03b1001f3d7046620860001"

res = page.evaluate(
    """(t) => {
      const cands = [...document.querySelectorAll("li, div, span")].filter(e => {
        const r = e.getBoundingClientRect();
        const x = (e.innerText||"").trim();
        return r.width > 0 && r.height > 0 && x === t;
      });
      if (!cands.length) return {err: "no-option"};
      cands.sort((a, b) => (a.getBoundingClientRect().width*a.getBoundingClientRect().height) - (b.getBoundingClientRect().width*b.getBoundingClientRect().height));
      const e = cands[0];
      const r = e.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
    }""",
    answer,
)
if res.get("err"):
    print("option not visible:", answer)
    b.close()
    sys.exit(1)
print("clicking option at", res)
page.mouse.click(res["x"], res["y"])
time.sleep(1.5)
state = page.evaluate(
    "id => { const b = document.getElementById(id); return b ? b.innerText.trim() : 'gone'; }",
    btn_id.replace("primaryQuestionnaire--", ""),
)
print("button now shows:", state)
b.close()
