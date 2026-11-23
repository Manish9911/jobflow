import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

link = f.locator("a:has-text('Add More (Professional Experience)')").last
link.scroll_into_view_if_needed()
link.click()
time.sleep(4)

out = f.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll("input[name*='rcf3212'], select[name*='rcf3212'], input[name*='rcf3218'], select[name*='rcf3218']").forEach(e => res.push(e.name));
  return res;
}""")
print("rows now:", out)
b.close()
