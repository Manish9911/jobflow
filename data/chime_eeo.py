import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "chime/jobs" in p.url)
time.sleep(3)

def pick(id, sub):
    e = page.locator('[id="' + id + '"]') if id[0].isdigit() else page.locator('#' + id)
    e.scroll_into_view_if_needed()
    e.click()
    time.sleep(1.2)
    page.keyboard.type(sub, delay=40)
    time.sleep(1.8)
    r = page.evaluate(r"""(args) => {
      const lists = [...document.querySelectorAll('[role=listbox] li, [class*=option], [class*=list] li, ul li')].filter(l => l.offsetParent !== null && l.innerText.trim().length > 0 && l.innerText.length < 80);
      if (!lists.length) return 'no opts';
      let hit = lists.find(l => l.innerText.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) hit = lists.find(l => l.innerText.toLowerCase().includes(args[1].toLowerCase()));
      if (!hit) return 'no match: ' + lists.slice(0, 12).map(l => l.innerText.trim()).join(' | ').slice(0, 250);
      hit.click();
      return 'picked: ' + hit.innerText.trim();
    }""", [id, sub])
    time.sleep(1.0)
    return r

tasks = [
    ('4024620002', 'Male'),
    ('4024621002', 'Asian'),
    ('4024622002', 'Straight'),
    ('4024623002', 'No'),
    ('4024624002', 'No'),
]
for tid, opt in tasks:
    print(tid, '->', opt, ':', pick(tid, opt))
b.close()
