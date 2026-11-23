import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "transonic.com/careers" in p.url)

resp_log = []
def on_resp(r):
    if "hsforms" in r.url or "submission" in r.url:
        body = ""
        try:
            body = r.text()[:300]
        except Exception:
            pass
        resp_log.append({"url": r.url[:100], "status": r.status, "body": body})
page.on("response", on_resp)

btn = page.locator("#hsForm_a5c590ce-9def-4cc4-82c7-ad4432cacd4a_3658 input[type=submit], #hsForm_a5c590ce-9def-4cc4-82c7-ad4432cacd4a_3658 button[type=submit]")
btn.scroll_into_view_if_needed()
btn.click()
time.sleep(20)
print("responses:", json.dumps(resp_log, indent=1))
# success message?
out = page.evaluate(r"""() => {
  const ok = document.querySelector('.hs-form-confirmation, .form-confirmation, #form .success, [class*="confirmation"]');
  return {
    conf: ok ? ok.innerText.trim().slice(0, 300) : null,
    body_top: document.body.innerText.slice(0, 500),
  };
}""")
print(json.dumps(out, indent=1))
b.close()
