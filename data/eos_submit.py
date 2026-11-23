import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

btn = page.evaluate(
    """() => {
      const b = [...document.querySelectorAll("button")].find(x => (x.innerText||'').trim() === 'Submit' && x.getBoundingClientRect().width > 0);
      if (!b) return null;
      b.scrollIntoView({block: 'center'});
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
    }"""
)
print("submit btn:", btn)
if btn:
    page.mouse.click(btn["x"], btn["y"])
    time.sleep(20)
print("URL now:", page.url)
txt = page.evaluate("() => document.body.innerText")
print("PAGE:", txt[:1800])
b.close()
