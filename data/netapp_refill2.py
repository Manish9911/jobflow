import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

# 437: experience extending complex systems -> Yes
def click_radio(gid, text):
    return page.evaluate(r"""(args) => {
      const g = document.getElementById(args[0]);
      if (!g) return 'no group';
      const labels = [...g.querySelectorAll('.radioLabel')];
      const hit = labels.find(l => l.innerText.trim() === args[1]);
      if (!hit) return 'no radio';
      const radio = hit.closest('.globalRadio').querySelector('[id*="_radio"]');
      radio.click();
      return 'clicked ' + args[1];
    }""", [gid, text])
print('437 experience:', click_radio('437:', 'Yes'))
time.sleep(1)

# --- paginated picklists: map by aria-label
picks = page.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('.rcmpaginatedselectbutton').forEach(e => {
    const al = (e.getAttribute('aria-label') || '').trim();
    const forid = (e.getAttribute('for') || '');
    const inp = forid ? document.getElementById(forid) : null;
    res.push({btn: e.id, al: al.slice(0, 50), forid, listid: inp ? inp.getAttribute('aria-controls') : null, val: inp ? inp.value : ''});
  });
  return res;
}""")
for p in picks:
    print(p['btn'], '|', p['al'], '| forid', p['forid'], '| listid', p['listid'])

def pick(forid, listid, text):
    inp = page.locator('[id="' + forid + '"]')
    inp.scroll_into_view_if_needed()
    inp.click()
    time.sleep(1.0)
    page.keyboard.type(text, delay=40)
    time.sleep(1.8)
    r = page.evaluate(r"""(args) => {
      const ul = document.getElementById(args[0]);
      if (!ul) return 'no list';
      const lis = [...ul.querySelectorAll('li, [role=option]')];
      if (!lis.length) return 'no lis';
      let hit = lis.find(l => l.innerText.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) hit = lis.find(l => l.innerText.toLowerCase().includes(args[1].toLowerCase()));
      if (!hit) return 'no match: ' + lis.map(l => l.innerText.trim()).join(' | ').slice(0, 200);
      hit.click();
      return 'picked: ' + hit.innerText.trim();
    }""", [listid, text])
    time.sleep(1.2)
    return r

plan = {
    'Current State': 'Tennessee',
    'sponsorship for employment': 'Yes',
    'Highest Level of Education': 'Master',
    'Gender': 'Male',
    'Ethnicity': 'Asian',
    'Veteran Status': 'Not a protected',
    'military spouse': 'Not applicable',
    'associated with NetApp': 'No',
    'restrictive covenants': 'No',
    'Disability Status': 'Do not wish',
}
for p in picks:
    for key, opt in plan.items():
        if key.lower() in p['al'].lower():
            if p['listid']:
                print(p['al'][:40], '->', opt, ':', pick(p['forid'], p['listid'], opt))
            else:
                print(p['al'][:40], '-> NO LISTID, forid', p['forid'])
b.close()
