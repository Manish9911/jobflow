import time, json
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "rhinogram.com" in p.url)
page.bring_to_front()
time.sleep(1)
btns = page.evaluate(
    """() => [...document.querySelectorAll("a, button")].filter(e => e.getBoundingClientRect().width > 0).map(e => ({t: (e.innerText||"").trim().slice(0, 40), href: e.href || ""})).filter(x => /apply|career|job/i.test(x.t + x.href))"""
)
print(json.dumps(btns, indent=1))
b.close()
