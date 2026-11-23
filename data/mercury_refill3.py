import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)

def getf():
    return next(ff for ff in page.frames if "in_iframe=1" in ff.url)

time.sleep(3)
f = getf()

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
def pick_dd(fr, name, query, wait=3.0):
    fr.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
    time.sleep(0.4)
    anchor = fr.locator('a[id="' + name + '_icimsDropdown"]')
    if anchor.count() == 0:
        return 'no anchor'
    anchor.first.click()
    time.sleep(1.0)
    fok = fr.evaluate(JS_FOCUS, name)
    if fok != 'focused':
        return fok
    time.sleep(0.5)
    page.keyboard.type(query, delay=60)
    time.sleep(wait)
    out = fr.evaluate(JS_LI, [name, query])
    time.sleep(1.0)
    return out

def set_text(fr, name, val):
    return fr.evaluate("""(a) => {
      const e = document.querySelector("input[name='" + a[0] + "']");
      if (!e) return 'no el';
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [name, val])

print('state:', pick_dd(f, '-1_PersonProfileFields.AddressState', 'Tennessee'))
time.sleep(1.0)
print('degree:', pick_dd(f, '-1_CandProfileFields.Degree', 'MS'))
time.sleep(1.0)
print('major:', pick_dd(f, '-1_CandProfileFields.Major', 'Computer Info. Sys.'))
time.sleep(1.0)
# find current emp prefix for currrole
pref = f.evaluate(r"""() => {
  const e = document.querySelector("input[name*='_PersonProfileFields.rcf3212']");
  return e ? e.name.split('_PersonProfileFields')[0] : null;
}""")
print('emp prefix:', pref)
if pref:
    print('currrole:', pick_dd(f, pref + '_PersonProfileFields.rcf3269', 'Yes'))
time.sleep(1.0)
# resume
f = getf()
fi = f.query_selector("input[type='file']")
if fi:
    fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
    print('resume set, waiting for parse...')
    time.sleep(18)
# address text LAST
f = getf()
time.sleep(2)
print('street:', set_text(f, '-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
print('city:', set_text(f, '-1_PersonProfileFields.AddressCity', 'Collierville'))
print('zip:', set_text(f, '-1_PersonProfileFields.AddressZip', '38017'))
time.sleep(1.5)
f = getf()
v = f.evaluate(r"""() => {
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  const fi = document.querySelector("input[type='file']");
  const btn = document.querySelector("input[name=profileButton]");
  const ta = document.querySelector("textarea[name='h-captcha-response']");
  return {
    street: t('-1_PersonProfileFields.AddressStreet1'), city: t('-1_PersonProfileFields.AddressCity'),
    zip: t('-1_PersonProfileFields.AddressZip'), state: s('-1_PersonProfileFields.AddressState'),
    degree: s('-1_CandProfileFields.Degree'), major: s('-1_CandProfileFields.Major'),
    first: t('PersonProfileFields.FirstName'), last: t('PersonProfileFields.LastName'),
    phone: t('-1_PersonProfileFields.PhoneNumber'), consent: s('rcf3553'),
    school: s('-1_CandProfileFields.School'), source: s('rcf3048'),
    resume: fi && fi.files && fi.files.length ? fi.files[0].name : null,
    btnDisabled: btn ? btn.disabled : null, token: ta ? ta.value : null,
  };
}""")
print(json.dumps(v, indent=1))
b.close()
