import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mercuryinsurance" in p.url and "candidate" in p.url)

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

# 1) state dropdown
f.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
time.sleep(0.4)
f.locator('a[id="-1_PersonProfileFields.AddressState_icimsDropdown"]').first.click()
time.sleep(1.0)
print('focus:', f.evaluate(JS_FOCUS, '-1_PersonProfileFields.AddressState'))
time.sleep(0.4)
page.keyboard.type('Tennessee', delay=60)
time.sleep(3.0)
print('state:', f.evaluate(JS_LI, ['-1_PersonProfileFields.AddressState', 'Tennessee']))
time.sleep(4.0)

# 2) FRESH frame after re-render
f = getf()
time.sleep(1)
fi = f.query_selector("input[type='file']")
print('file input found:', bool(fi))
if fi:
    fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
    time.sleep(4.0)
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
print('street:', set_text(f, '-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
print('city:', set_text(f, '-1_PersonProfileFields.AddressCity', 'Collierville'))
print('zip:', set_text(f, '-1_PersonProfileFields.AddressZip', '38017'))
time.sleep(2.0)
f = getf()
v = f.evaluate(r"""() => {
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const s = (n) => { const e = document.querySelector("select[name='" + n + "']"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; };
  const fi = document.querySelector("input[type='file']");
  return {street: t('-1_PersonProfileFields.AddressStreet1'), city: t('-1_PersonProfileFields.AddressCity'),
          zip: t('-1_PersonProfileFields.AddressZip'), state: s('-1_PersonProfileFields.AddressState'),
          resume: fi && fi.files && fi.files.length ? fi.files[0].name : null,
          hasSubmit: !!document.querySelector("input[name=profileButton]")};
}""")
print('PRE-SUBMIT:', json.dumps(v))

# 3) POST capture + submit
log = []
def on_resp(r):
    if r.request.method == 'POST':
        try:
            body = r.text()[:2000]
        except Exception:
            body = '<err>'
        log.append({'u': r.request.url[:120], 's': r.status, 'body': body})
page.on('response', on_resp)
f.locator('input[name=profileButton]').click()
time.sleep(40)
print('POST count:', len(log))
for e in log:
    print('POST', e['s'], e['u'])
    print('BODY:', e['body'][:1800])
    print('---')
b.close()
