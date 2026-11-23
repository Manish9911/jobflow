import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "highroller-careers.com" in p.url)
page.bring_to_front()
time.sleep(1)
btn = page.evaluate(
    """() => {
      const b = [...document.querySelectorAll("a, button")].find(x => (x.innerText||'').trim().toLowerCase() === 'apply' && x.getBoundingClientRect().width > 0);
      if (!b) return null;
      b.scrollIntoView({block: 'center'});
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), href: b.href || ""};
    }"""
)
print("apply btn:", btn)
if btn and not btn["href"]:
    page.mouse.click(btn["x"], btn["y"])
    time.sleep(8)
print("URL now:", page.url)
inputs = page.evaluate(
    """() => [...document.querySelectorAll("input, textarea, select")].filter(e => e.getBoundingClientRect().width > 0).map(e => ({tag: e.tagName, id: e.id, name: e.name, type: e.type, ph: e.placeholder || ""}))"""
)
print(json.dumps(inputs, indent=1))
b.close()
