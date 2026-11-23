import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

name = "5397892_PersonProfileFields.rcf3218"
a = f.locator(f'[id="{name}_icimsDropdown"]')
a.scroll_into_view_if_needed()
a.click()
time.sleep(2)
print("focused:", f.evaluate("() => document.activeElement ? document.activeElement.tagName + '#' + document.activeElement.id : 'none'"))
print("ctnr:", f.evaluate("(n) => document.getElementById(n + '_icimsDropdown_ctnr').className", name))
b.close()
