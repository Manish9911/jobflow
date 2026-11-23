import time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "highroller-careers.com" in p.url)
txt = page.evaluate("() => document.body.innerText")
i = txt.find("Cover letter")
print(txt[i:i+700])
b.close()
