import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "anthropic/jobs" in p.url)
time.sleep(3)

ids = ['question_15797027008', 'question_15797028008', 'question_15797029008', 'question_15797030008', 'question_15797032008', 'question_15797033008', 'question_15797036008', 'question_15797037008', 'question_15797038008', 'question_18372122008', 'question_18374786008', 'gender', 'hispanic_ethnicity', 'veteran_status', 'country']
res = {}
for iid in ids:
    try:
        e = page.locator('[id="' + iid + '"]')
        if e.count() == 0:
            res[iid] = 'missing'
            continue
        e.scroll_into_view_if_needed()
        e.click()
        time.sleep(1.2)
        opts = page.evaluate(r"""() => {
          const o = [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
          return o.map(x => x.innerText.trim());
        }""")
        res[iid] = opts[:12] if opts else 'NO OPTIONS OPEN'
        page.keyboard.press('Escape')
        time.sleep(0.6)
    except Exception as ex:
        res[iid] = 'ERR ' + str(ex)[:60]
print(json.dumps(res, indent=1))
b.close()
