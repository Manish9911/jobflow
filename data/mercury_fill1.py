import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)

def set_text(name, val):
    return f.evaluate("""(a) => {
      const e = document.querySelector("input[name='" + a[0] + "']");
      if (!e) return 'no el';
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      return 'ok';
    }""", [name, val])

def set_select(name, val):
    return f.evaluate("""(a) => {
      const e = document.querySelector("select[name='" + a[0] + "']");
      if (!e) return 'no el';
      const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('change', {bubbles: true}));
      return 'ok';
    }""", [name, val])

def set_select_by_text(name, txt):
    return f.evaluate("""(a) => {
      const e = document.querySelector("select[name='" + a[0] + "']");
      if (!e) return 'no el';
      const hit = [...e.options].find(o => o.text.trim() === a[1]);
      if (!hit) return 'no opt: ' + [...e.options].map(o=>o.text.trim()).slice(0,8).join(',');
      const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
      s.call(e, hit.value);
      e.dispatchEvent(new Event('change', {bubbles: true}));
      return 'ok';
    }""", [name, txt])

print('first:', set_text('PersonProfileFields.FirstName', 'Manish'))
print('last:', set_text('PersonProfileFields.LastName', 'Badugu'))
print('source:', set_select_by_text('rcf3048', 'Company Website'))
print('phonetype:', set_select('-1_PersonProfileFields.PhoneType', '15145'))
print('phone:', set_text('-1_PersonProfileFields.PhoneNumber', '19408436058'))
print('consent:', set_select_by_text('rcf3553', 'I do not consent'))
print('addrtype:', set_select('-1_PersonProfileFields.AddressType', '15149'))
print('street:', set_text('-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
print('city:', set_text('-1_PersonProfileFields.AddressCity', 'Collierville'))
print('zip:', set_text('-1_PersonProfileFields.AddressZip', '38017'))
# source follow-up — check options now
src9 = f.evaluate(r"""() => { const e = document.querySelector("select[name='rcf3049']"); return e ? [...e.options].map(o=>o.text.trim()).slice(0,10) : null; }""")
print('rcf3049 opts now:', src9)
# employment row 1: Verizon
print('emp1:', set_text('-1_PersonProfileFields.rcf3212', 'Verizon Communications'))
print('title1:', set_text('-1_PersonProfileFields.rcf3213', 'Sr. Java Full Stack Developer'))
print('city1:', set_text('-1_PersonProfileFields.rcf3216', 'New York'))
print('startm:', set_select('-1_PersonProfileFields.rcf3214_Month', '07'))
print('starty:', set_text('-1_PersonProfileFields.rcf3214_Year', '2025'))
print('currrole:', set_select_by_text('-1_PersonProfileFields.rcf3269', 'Yes'))
# login / password
print('login:', set_text('PersonProfileFields.Login', 'badugu.m7@gmail.com'))
for p in ('PersonProfileFields.Password', 'PersonProfileFields.Password_Confirm'):
    print(p, ':', set_text(p, 'Manish@2026!x9k'))
# resume
fi = f.query_selector("input[type='file']")
print('file input:', bool(fi))
fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
time.sleep(2)
b.close()
print('DONE phase 1 (plain fields)')
