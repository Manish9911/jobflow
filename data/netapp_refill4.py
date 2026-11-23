import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

def pick(btnid, text):
    inp = page.locator('[id="' + btnid + ':_input"]')
    inp.scroll_into_view_if_needed()
    inp.click()
    time.sleep(0.8)
    page.keyboard.type(text, delay=40)
    time.sleep(1.8)
    r = page.evaluate(r"""(args) => {
      const ul = document.getElementById(args[0] + ':_listSelect');
      if (!ul) return 'no list';
      const lis = [...ul.querySelectorAll('li, [role=option]')];
      if (!lis.length) return 'no lis';
      let hit = lis.find(l => l.innerText.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) hit = lis.find(l => l.innerText.toLowerCase().includes(args[1].toLowerCase()));
      if (!hit) return 'no match: ' + lis.map(l => l.innerText.trim()).join(' | ').slice(0, 250);
      hit.click();
      return 'picked: ' + hit.innerText.trim();
    }""", [str(int(btnid) + 1), text])
    time.sleep(1.2)
    v = page.evaluate(r"""(id) => { const e = document.getElementById(id + ':_input'); return e ? e.value : null; }""", btnid)
    return r + f' [val={v}]'

# re-pick all (safe: overwrites), full option text where known
tasks = [
    ('424', 'Tennessee'),
    ('500', 'Yes'),
    ('535', "Master's Degree"),
    ('554', 'Male'),
    ('561', 'Asian'),
    ('568', 'I am not a protected veteran'),
    ('575', 'Not applicable'),
    ('582', 'No'),
    ('589', 'No'),
    ('612', 'I do not wish to answer'),
]
for btnid, opt in tasks:
    print(btnid, '->', opt, ':', pick(btnid, opt))
b.close()
