import json, time, glob
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "affirm/jobs/8041432003" in p.url)
time.sleep(3)

def set_text(id, val):
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

def pick(id, text):
    e = page.locator('[id="' + id + '"]')
    e.scroll_into_view_if_needed()
    e.click()
    time.sleep(1.0)
    page.keyboard.type(text, delay=50)
    time.sleep(1.5)
    ok = page.evaluate(r"""(a) => {
      const lb = document.getElementById('react-select-' + a[0] + '-listbox');
      const o = lb ? [...lb.querySelectorAll('[role=option]')] : [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
      let hit = o.find(x => x.innerText.trim().toLowerCase() === a[1].toLowerCase());
      if (!hit) hit = o.find(x => x.innerText.toLowerCase().includes(a[1].toLowerCase()));
      if (!hit) {
        // clear stuck text and re-list
        const inp = document.getElementById(a[0]);
        const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        s.call(inp, '');
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        const o2 = lb ? [...lb.querySelectorAll('[role=option]')] : [];
        return 'retry-needed: ' + o2.slice(0, 8).map(x => x.innerText.trim()).join('|');
      }
      hit.click();
      return 'picked: ' + hit.innerText.trim().slice(0, 45);
    }""", [id, text])
    time.sleep(0.8)
    return ok

print('first:', set_text('first_name', 'Manish'))
print('last:', set_text('last_name', 'Badugu'))
print('email:', set_text('email', 'badugu.m7@gmail.com'))
print('phone:', set_text('phone', '+1 940-843-6058'))
print('pref:', set_text('question_33220215003', 'Manish'))
print('company:', set_text('question_33220214003', 'Polaris'))
print('linkedin:', set_text('question_33220213003', 'https://www.linkedin.com/in/badugu-manish-2241/'))
print('github:', set_text('question_33220222003', 'https://github.com/Manish9911'))
pdfs = glob.glob('data/exports/affirm/*.pdf')
page.locator('#resume').set_input_files(pdfs[0])
print('resume set')
time.sleep(2)

tasks = [
    ('country', 'United States'),
    ('question_33220217003', 'He/him'),
    ('question_33252095003', 'Yes'),
    ('question_33252096003', 'Yes'),
    ('question_33252097003', 'No'),
    ('question_33220220003', 'LinkedIn'),
    ('question_33220221003', 'I have not previously'),
]
for tid, opt in tasks:
    r = pick(tid, opt)
    print(tid, ':', r)
    if 'retry-needed' in r:
        # clear and pick from shown options
        ok = page.evaluate(r"""(a) => {
          const lb = document.getElementById('react-select-' + a[0] + '-listbox');
          if (!lb) return 'no lb';
          const o = [...lb.querySelectorAll('[role=option]')];
          let hit = o.find(x => x.innerText.trim().toLowerCase() === a[1].toLowerCase());
          if (!hit) hit = o.find(x => x.innerText.toLowerCase().includes(a[1].slice(0, 6).toLowerCase()));
          if (!hit) return 'no match2: ' + o.slice(0, 8).map(x => x.innerText.trim()).join('|');
          hit.click();
          return 'picked: ' + hit.innerText.trim().slice(0, 45);
        }""", [tid, opt])
        print('  retry:', ok)
b.close()
