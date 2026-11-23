import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers.garmin.com/jobs/20463" in p.url)
btn = page.locator("a:has-text('APPLY'), button:has-text('APPLY')").first
btn.click()
time.sleep(15)
# find the ICIMS tab
pages = [p for p in ctx.pages if "careers-garmin.icims.com" in p.url]
print("icims tabs:", [p.url[:100] for p in pages])
page = pages[-1] if pages else None
if not page:
    print("no icims tab"); b.close(); raise SystemExit
time.sleep(8)
print("URL:", page.url[:120])
for ff in page.frames:
    try:
        txt = ff.evaluate("() => document.body ? document.body.innerText.slice(0, 500) : ''")
        if txt.strip():
            print("FRAME:", txt.replace(chr(10), " | ")[:450])
    except Exception:
        pass
b.close()
