import json, time, glob
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "workos" in p.url)
time.sleep(3)

def setv(id, val):
    return page.evaluate("""(a) => {
      const e = document.getElementById(a[0]);
      if (!e) return 'no el';
      e.focus();
      const proto = e.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
      const s = Object.getOwnPropertyDescriptor(proto, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [id, val])

print('name:', setv('_systemfield_name', 'Manish Badugu'))
print('email:', setv('_systemfield_email', 'badugu.m7@gmail.com'))
print('phone:', setv('c2a4aa11-db18-4fcd-b477-388072c64709', '+1 940-843-6058'))
print('linkedin:', setv('dc476a03-1066-4481-85a8-38484fa4df94', 'https://www.linkedin.com/in/badugu-manish-2241/'))
print('github:', setv('64ec1404-cb35-44e2-9c16-f39a866a599a', 'https://github.com/Manish9911'))
pdfs = glob.glob('data/exports/workos2/*.pdf')
page.locator('#_systemfield_resume').set_input_files(pdfs[0])
print('resume set')
time.sleep(2)

# location autocomplete
loc = page.locator('.ashby-application-form-field-entry[data-field-path="_systemfield_location"] input')
loc.scroll_into_view_if_needed()
loc.click()
time.sleep(1)
page.keyboard.type('Collierville, TN', delay=60)
time.sleep(2)
r = page.evaluate(r"""() => {
  const o = [...document.querySelectorAll('[role=option], [role=listbox] li')].filter(x => x.offsetParent !== null);
  const hit = o.find(x => x.innerText.toLowerCase().includes('collierville'));
  if (!hit) return 'no opt: ' + o.slice(0,5).map(x => x.innerText.trim()).join('|');
  hit.click();
  return 'picked: ' + hit.innerText.trim();
}""")
print('location:', r)
time.sleep(1)

# yes/no buttons
for path in ['10744b0e-6aa0-4391-a525-c34c03f42e8b', '49f0e39a-e038-4248-b3e7-4c7dec0c31c2']:
    r2 = page.evaluate(r"""(p) => {
      const f = document.querySelector('.ashby-application-form-field-entry[data-field-path="' + p + '"]');
      if (!f) return 'no field';
      const btn = f.querySelector('button[data-option="yes"]');
      btn.scrollIntoView({block: 'center'});
      btn.click();
      return 'yes';
    }""", path)
    print(path[:8], r2)
    time.sleep(0.8)
b.close()
