import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)
txt = page.evaluate("() => document.body.innerText")
i = txt.find("How do you know if you have a disability?")
print(txt[i:i+2600])
print("===INPUTS===")
print(json.dumps(page.evaluate(
    """() => [...document.querySelectorAll("input, select, textarea")].filter(e => e.getBoundingClientRect().width > 0).map(e => ({tag: e.tagName, id: e.id, type: e.type, val: (e.value||"").slice(0,40), ph: e.placeholder||""}))"""
), indent=1))
b.close()
