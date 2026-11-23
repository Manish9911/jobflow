import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "anthropic/jobs" in p.url)
time.sleep(3)

def pick(id, text):
    e = page.locator('[id="' + id + '"]')
    e.scroll_into_view_if_needed()
    e.click()
    time.sleep(1.0)
    page.keyboard.type(text, delay=60)
    time.sleep(1.5)
    ok = page.evaluate(r"""(t) => {
      const o = [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
      let hit = o.find(x => x.innerText.trim().toLowerCase() === t.toLowerCase());
      if (!hit) hit = o.find(x => x.innerText.toLowerCase().includes(t.toLowerCase()));
      if (!hit) return 'no match: ' + o.slice(0,8).map(x => x.innerText.trim()).join('|');
      hit.click();
      return 'picked: ' + hit.innerText.trim().slice(0, 60);
    }""", text)
    time.sleep(0.8)
    return ok

tasks = [
    ('question_15797027008', 'Yes'),
    ('question_15797030008', 'Yes'),
    ('question_15797032008', 'Yes'),
    ('question_15797033008', 'Yes'),
    ('question_15797036008', 'No'),
    ('question_15797038008', 'No'),
    ('question_18372122008', 'I will read'),
    ('question_18374786008', 'I understand and agree'),
    ('gender', 'Male'),
    ('hispanic_ethnicity', 'No'),
    ('veteran_status', 'I am not a protected veteran'),
]
for tid, opt in tasks:
    print(tid, ':', pick(tid, opt))
b.close()
