import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)

JS_LI = r"""(a) => {
  const name = a[0], q = a[1];
  const ul = document.querySelector('[id="' + name + '_dropdown-results"]');
  if (!ul) return 'no ul';
  const lis = [...ul.querySelectorAll('li')];
  if (!lis.length) return 'no lis: ' + ul.innerText.slice(0, 100);
  let hit = lis.find(li => li.innerText.trim().toLowerCase() === q.toLowerCase());
  if (!hit) hit = lis.find(li => li.innerText.toLowerCase().includes(q.toLowerCase()));
  if (!hit) return 'no match: ' + lis.map(l => l.innerText.trim()).join(' | ').slice(0, 150);
  hit.click();
  return 'clicked: ' + hit.innerText.trim();
}"""
JS_FOCUS = r"""(n) => {
  const i = document.querySelector('[id="' + n + '_icimsDropdown_ctnr"] input.dropdown-search');
  if (!i) return 'no input';
  i.focus();
  return 'focused';
}"""

def pick_dd(name, query, wait=3.0):
    f.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
    time.sleep(0.4)
    anchor = f.locator('a[id="' + name + '_icimsDropdown"]')
    if anchor.count() == 0:
        return 'no anchor'
    anchor.first.click()
    time.sleep(1.0)
    fok = f.evaluate(JS_FOCUS, name)
    if fok != 'focused':
        return fok
    time.sleep(0.5)
    page.keyboard.type(query, delay=60)
    time.sleep(wait)
    out = f.evaluate(JS_LI, [name, query])
    time.sleep(1.0)
    return out

# check major options first
maj = f.evaluate(r"""() => {
  const ul = document.querySelector('[id="-1_CandProfileFields.Major_dropdown-results"]');
  return ul ? [...ul.querySelectorAll('li')].map(l => l.innerText.trim()).filter(t => /computer/i.test(t)).slice(0, 12) : null;
}""")
print('major computer options:', maj)

print('state:', pick_dd('-1_PersonProfileFields.AddressState', 'Tennessee', wait=4.0))
print('VERIFY state =>', f.evaluate(r"""() => { const e = document.querySelector("select[name='-1_PersonProfileFields.AddressState']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; }"""))
b.close()
