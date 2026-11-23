import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

def menu_open():
    return page.evaluate(
        """() => {
          const cands = [...document.querySelectorAll("li, div, span")].filter(e => {
            const r = e.getBoundingClientRect();
            const x = (e.innerText||"").trim();
            return r.width > 100 && r.height > 12 && x.indexOf("VETERAN") !== -1;
          });
          return cands.length;
        }"""
    )

for i in range(4):
    page.locator("#personalInfoUS--veteranStatus").click(timeout=8000)
    time.sleep(2)
    n = menu_open()
    print(f"attempt {i+1}: veteran-option elements visible: {n}")
    if n:
        break

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
    print("STILL no option")
    b.close()
    raise SystemExit(1)
page.mouse.click(res["x"], res["y"])
time.sleep(1.5)
state = page.evaluate("() => { const b = document.getElementById('personalInfoUS--veteranStatus'); return b ? b.innerText.trim() : 'gone'; }")
print("veteran now:", state)
b.close()
