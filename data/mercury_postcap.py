import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mercuryinsurance" in p.url and "candidate" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)

# first re-fill everything (state dd, file, address text)
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
f.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
time.sleep(0.4)
f.locator('a[id="-1_PersonProfileFields.AddressState_icimsDropdown"]').first.click()
time.sleep(1.0)
f.evaluate(JS_FOCUS, '-1_PersonProfileFields.AddressState')
time.sleep(0.4)
page.keyboard.type('Tennessee', delay=60)
time.sleep(3.0)
print('state:', f.evaluate(JS_LI, ['-1_PersonProfileFields.AddressState', 'Tennessee']))
time.sleep(2.0)
fi = f.query_selector("input[type='file']")
fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
time.sleep(3.0)
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
set_text('-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV')
set_text('-1_PersonProfileFields.AddressCity', 'Collierville')
set_text('-1_PersonProfileFields.AddressZip', '38017')
time.sleep(1.5)

# capture POST
log = []
def on_resp(r):
    if r.request.method == 'POST':
        try:
            body = r.text()[:3000]
        except Exception:
            body = '<body err>'
        log.append({'u': r.request.url[:120], 's': r.status, 'body': body})
page.on('response', on_resp)
f.locator('input[name=profileButton]').click()
time.sleep(40)
for e in log:
    print('POST', e['s'], e['u'])
    print('BODY:', e['body'][:2500])
    print('---')
b.close()
