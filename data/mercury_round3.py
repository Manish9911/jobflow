import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mercuryinsurance" in p.url and "candidate" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)

JS_LI = r"""(a) => {
  const name = a[0], q = a[1];
  const ul = document.querySelector('[id="' + name + '_dropdown-results"]');
  if (!ul) return 'no ul';
  const lis = [...ul.querySelectorAll('li')];
  if (!lis.length) return 'no lis';
  let hit = lis.find(li => li.innerText.trim().toLowerCase() === q.toLowerCase());
  if (!hit) hit = lis.find(li => li.innerText.toLowerCase().includes(q.toLowerCase()));
  if (!hit) return 'no match: ' + lis.map(l => l.innerText.trim()).join(' | ').slice(0, 100);
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

print('currrole:', pick_dd('-1224135_PersonProfileFields.rcf3269', 'Yes'))
print('otherschool2:', f.evaluate("""(a) => {
  const e = document.querySelector("input[name='" + a[0] + "']");
  if (!e) return 'no el';
  e.focus();
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  s.call(e, a[1]);
  e.dispatchEvent(new Event('input', {bubbles: true}));
  e.dispatchEvent(new Event('change', {bubbles: true}));
  e.blur();
  return 'ok';
}""", ['-2_CandProfileFields.OtherSchool', 'Anurag Group of Institutions']))
time.sleep(1)
v = f.evaluate(r"""() => {
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  return {currrole: s('-1224135_PersonProfileFields.rcf3269'), os2: t('-2_CandProfileFields.OtherSchool'),
          street: t('-1_PersonProfileFields.AddressStreet1'), city: t('-1_PersonProfileFields.AddressCity'),
          zip: t('-1_PersonProfileFields.AddressZip'), state: s('-1_PersonProfileFields.AddressState')};
}""")
print(json.dumps(v, indent=1))
b.close()
