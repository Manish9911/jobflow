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
  if (!hit) return 'no match';
  hit.click();
  return 'clicked: ' + hit.innerText.trim();
}"""
JS_FOCUS = r"""(n) => {
  const i = document.querySelector('[id="' + n + '_icimsDropdown_ctnr"] input.dropdown-search');
  if (!i) return 'no input';
  i.focus();
  return 'focused';
}"""

# 1) state dropdown first (triggers re-render, wipes text)
f.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
time.sleep(0.4)
f.locator('a[id="-1_PersonProfileFields.AddressState_icimsDropdown"]').first.click()
time.sleep(1.0)
print('focus:', f.evaluate(JS_FOCUS, '-1_PersonProfileFields.AddressState'))
time.sleep(0.4)
page.keyboard.type('Tennessee', delay=60)
time.sleep(3.0)
print('state:', f.evaluate(JS_LI, ['-1_PersonProfileFields.AddressState', 'Tennessee']))
time.sleep(2.0)

# 2) resume file
fi = f.query_selector("input[type='file']")
fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
time.sleep(3.0)

# 3) address text fields
def set_text(name, val):
    return f.evaluate("""(a) => {
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
print('street:', set_text('-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
print('city:', set_text('-1_PersonProfileFields.AddressCity', 'Collierville'))
print('zip:', set_text('-1_PersonProfileFields.AddressZip', '38017'))
time.sleep(1.5)

# 4) final verify
v = f.evaluate(r"""() => {
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  const fi2 = document.querySelector("input[type='file']");
  return {
    street: t('-1_PersonProfileFields.AddressStreet1'), city: t('-1_PersonProfileFields.AddressCity'),
    zip: t('-1_PersonProfileFields.AddressZip'), state: s('-1_PersonProfileFields.AddressState'),
    country: s('-1_PersonProfileFields.AddressCountry'),
    school2: s('-2_CandProfileFields.School'), os2: t('-2_CandProfileFields.OtherSchool'),
    degree2: s('-2_CandProfileFields.Degree'), major2: s('-2_CandProfileFields.Major'),
    currrole: s('-1224135_PersonProfileFields.rcf3269'),
    resume: fi2 && fi2.files && fi2.files.length ? fi2.files[0].name : null,
  };
}""")
print(json.dumps(v, indent=1))
# 5) SUBMIT
f.locator('input[name=profileButton]').click()
time.sleep(35)
f2 = next((ff for ff in page.frames if 'in_iframe=1' in ff.url), None)
if f2:
    try:
        txt = f2.evaluate('() => document.body ? document.body.innerText.slice(0, 400) : ""')
        print('AFTER:', txt.replace(chr(10), ' | ')[:380])
    except Exception as e:
        print('AFTER: frame gone (navigation?)', page.url[:120])
b.close()
