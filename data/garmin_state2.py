"""Check Garmin iCIMS candidate-profile form state (Playwright over CDP)."""
import json
import time

import playwright.sync_api as pw

b = pw.sync_playwright().start()
try:
    browser = b.chromium.connect_over_cdp("http://127.0.0.1:9334")
    ctx = browser.contexts[0]
    page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
    f = next((ff for ff in page.frames if "in_iframe=1" in ff.url), None)
    if f is None:
        f = page.frame(name="icims_content_iframe") or page.main_frame
    time.sleep(3)
    out = f.evaluate(r"""() => {
      const t = document.body.innerText.replace(/\n{2,}/g, '\n').slice(0, 1500);
      const fields = [...document.querySelectorAll('input:not([type=hidden]), select, textarea')]
        .map(e => e.tagName[0] + (e.type || '') + ':' + (e.name || e.id || '').slice(0, 50)
          + '=' + String(e.value || '').slice(0, 25) + (e.required ? '*' : ''));
      const btns = [...document.querySelectorAll('input[type=submit], button')]
        .map(e => (e.value || e.innerText || '').trim()).filter(Boolean);
      return {title: document.title, fields: fields.slice(0, 60), btns: [...new Set(btns)].slice(0, 12), text: t};
    }""")
    print(json.dumps(out, indent=1))
finally:
    b.stop()
