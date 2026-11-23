import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)

def getf():
    return next(ff for ff in page.frames if "in_iframe=1" in ff.url)

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

f = getf()
time.sleep(3)
# check emp rows (parse state)
def emp_state(fr):
    return fr.evaluate(r"""() => {
      const e = document.querySelector("input[name*='_PersonProfileFields.rcf3212']");
      return e ? {found: true, val: e.value, prefix: e.name.split('_PersonProfileFields')[0]} : {found: false};
    }""")
st = emp_state(f)
print('emp now:', st)
if not st.get('found') or not st.get('val'):
    # resume may need re-set
    fi = f.query_selector("input[type='file']")
    if fi:
        fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
        print('resume re-set, polling for parse...')
    deadline = time.time() + 90
    parsed = False
    while time.time() < deadline:
        time.sleep(6)
        try:
            f = getf()
            st = emp_state(f)
        except Exception:
            continue
        if st.get('val'):
            parsed = True
            break
        print('  ... still parsing', st)
    print('parsed:', parsed, st)
time.sleep(5)
f = getf()
# final dropdown sequence
print('state:', pick_dd(f, '-1_PersonProfileFields.AddressState', 'Tennessee'))
time.sleep(1.0)
print('degree:', pick_dd(f, '-1_CandProfileFields.Degree', 'MS'))
time.sleep(1.0)
print('major:', pick_dd(f, '-1_CandProfileFields.Major', 'Computer Info. Sys.'))
time.sleep(1.0)
pref = f.evaluate(r"""() => { const e = document.querySelector("input[name*='_PersonProfileFields.rcf3212']"); return e ? e.name.split('_PersonProfileFields')[0] : null; }""")
if pref:
    print('currrole:', pick_dd(f, pref + '_PersonProfileFields.rcf3269', 'Yes'))
time.sleep(6)
f = getf()
print('street:', set_text(f, '-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
print('city:', set_text(f, '-1_PersonProfileFields.AddressCity', 'Collierville'))
print('zip:', set_text(f, '-1_PersonProfileFields.AddressZip', '38017'))
time.sleep(3)
f = getf()
v = f.evaluate(r"""() => {
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  const btn = document.querySelector("input[name=profileButton]");
  return {
    street: t('-1_PersonProfileFields.AddressStreet1'), city: t('-1_PersonProfileFields.AddressCity'),
    zip: t('-1_PersonProfileFields.AddressZip'), state: s('-1_PersonProfileFields.AddressState'),
    degree: s('-1_CandProfileFields.Degree'), major: s('-1_CandProfileFields.Major'),
    first: t('PersonProfileFields.FirstName'), last: t('PersonProfileFields.LastName'),
    school: s('-1_CandProfileFields.School'), consent: s('rcf3553'), source: s('rcf3048'),
    btnDisabled: btn ? btn.disabled : null,
  };
}""")
print(json.dumps(v, indent=1))
b.close()
