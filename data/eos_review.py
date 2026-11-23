import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)
txt = page.evaluate("() => document.body.innerText")
i = txt.rfind("Education")
print("TAIL:", txt[-1500:])
btns = page.evaluate(
    """() => [...document.querySelectorAll("button, a")].filter(e => e.getBoundingClientRect().width > 0).map(e => ({t: (e.innerText||"").trim().slice(0,50), tag: e.tagName})).filter(x => x.t)"""
)
print("BUTTONS:", json.dumps(btns))
chks = page.evaluate(
    """() => [...document.querySelectorAll("input[type=checkbox]")].filter(e => e.getBoundingClientRect().width > 0).map(e => ({id: e.id, checked: e.checked}))"""
)
print("CHECKBOXES:", json.dumps(chks))
b.close()
