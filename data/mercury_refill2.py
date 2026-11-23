import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)

def getf():
    return next(ff for ff in page.frames if "in_iframe=1" in ff.url)

time.sleep(3)
f = getf()

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

def selval(fr, name):
    return fr.evaluate(r"""(n) => {
      const e = document.querySelector("select[name='" + n + "']");
      return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null;
    }""", name)

# 1) plain text (will be wiped by dropdown re-renders; re-set at the end)
print('first:', set_text(f, 'PersonProfileFields.FirstName', 'Manish'))
print('last:', set_text(f, 'PersonProfileFields.LastName', 'Badugu'))
print('login:', set_text(f, 'PersonProfileFields.Login', 'badugu.m7@gmail.com'))
print('pw:', set_text(f, 'PersonProfileFields.Password', 'Manish@2026!x9k'))
print('pwc:', set_text(f, 'PersonProfileFields.Password_Confirm', 'Manish@2026!x9k'))
print('phone:', set_text(f, '-1_PersonProfileFields.PhoneNumber', '19408436058'))
# 2) country first (loads state list)
print('country:', pick_dd(f, '-1_PersonProfileFields.AddressCountry', 'United States'))
time.sleep(2.0)
f = getf()
print('state:', pick_dd(f, '-1_PersonProfileFields.AddressState', 'Tennessee'))
time.sleep(2.0)
# 3) education
print('school:', pick_dd(f, '-1_CandProfileFields.School', 'Christian Brothers'))
time.sleep(1.0)
print('degree:', pick_dd(f, '-1_CandProfileFields.Degree', 'MS'))
time.sleep(1.0)
print('major:', pick_dd(f, '-1_CandProfileFields.Major', 'Computer Info. Sys.'))
time.sleep(1.0)
# 4) consent
print('consent:', pick_dd(f, 'rcf3553', 'No'))
time.sleep(1.0)
# 5) resume (triggers parse re-render)
f = getf()
fi = f.query_selector("input[type='file']")
print('file input:', bool(fi))
if fi:
    fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
    time.sleep(15)
# 6) re-fetch frame, re-set all text fields, set source selects
f = getf()
time.sleep(2)
print('first2:', set_text(f, 'PersonProfileFields.FirstName', 'Manish'))
print('last2:', set_text(f, 'PersonProfileFields.LastName', 'Badugu'))
print('login2:', set_text(f, 'PersonProfileFields.Login', 'badugu.m7@gmail.com'))
print('pw2:', set_text(f, 'PersonProfileFields.Password', 'Manish@2026!x9k'))
print('pwc2:', set_text(f, 'PersonProfileFields.Password_Confirm', 'Manish@2026!x9k'))
print('phone2:', set_text(f, '-1_PersonProfileFields.PhoneNumber', '19408436058'))
print('street:', set_text(f, '-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
print('city:', set_text(f, '-1_PersonProfileFields.AddressCity', 'Collierville'))
print('zip:', set_text(f, '-1_PersonProfileFields.AddressZip', '38017'))
# source selects (native)
print('source:', f.evaluate("""() => { const e = document.querySelector("select[name='rcf3048']"); if (!e) return 'no el'; const hit = [...e.options].find(o => o.text.trim() === 'Company Website'); if (!hit) return 'no opt'; const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set; s.call(e, hit.value); e.dispatchEvent(new Event('change', {bubbles: true})); return 'ok'; }"""))
time.sleep(1.0)
print('source9:', f.evaluate("""() => { const e = document.querySelector("select[name='rcf3049']"); if (!e) return 'no el'; const hit = [...e.options].find(o => /no additional/i.test(o.text)); if (!hit) return 'no opt yet'; const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set; s.call(e, hit.value); e.dispatchEvent(new Event('change', {bubbles: true})); return 'ok'; }"""))
time.sleep(1.5)
f = getf()
# verify everything
v = f.evaluate(r"""() => {
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  const fi = document.querySelector("input[type='file']");
  const emp = [...document.querySelectorAll("input[name*='rcf3212']")].map(e => e.name + '=' + e.value);
  return {
    first: t('PersonProfileFields.FirstName'), last: t('PersonProfileFields.LastName'),
    email: t('PersonProfileFields.Email'), phone: t('-1_PersonProfileFields.PhoneNumber'),
    login: t('PersonProfileFields.Login'), pw: t('PersonProfileFields.Password') ? '***' : null,
    source: s('rcf3048'), source9: s('rcf3049'), consent: s('rcf3553'),
    street: t('-1_PersonProfileFields.AddressStreet1'), city: t('-1_PersonProfileFields.AddressCity'),
    zip: t('-1_PersonProfileFields.AddressZip'), country: s('-1_PersonProfileFields.AddressCountry'),
    state: s('-1_PersonProfileFields.AddressState'),
    school: s('-1_CandProfileFields.School'), degree: s('-1_CandProfileFields.Degree'),
    major: s('-1_CandProfileFields.Major'), grad: s('-1_CandProfileFields.IsGraduated'),
    resume: fi && fi.files && fi.files.length ? fi.files[0].name : null,
    emp,
  };
}""")
print(json.dumps(v, indent=1))
b.close()
