import json, time, glob
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "affirm/jobs/8197325003" in p.url)
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
      if (!hit) return 'nomatch: ' + o.slice(0, 8).map(x => x.innerText.trim()).join('|');
      hit.click();
      return 'picked: ' + hit.innerText.trim().slice(0, 45);
    }""", [id, text])
    time.sleep(0.8)
    return ok

print('first:', set_text('first_name', 'Manish'))
print('last:', set_text('last_name', 'Badugu'))
print('email:', set_text('email', 'badugu.m7@gmail.com'))
print('phone:', set_text('phone', '+1 940-843-6058'))
print('pref:', set_text('question_35351178003', 'Manish'))
print('company:', set_text('question_35351177003', 'Polaris'))
print('linkedin:', set_text('question_35351176003', 'https://www.linkedin.com/in/badugu-manish-2241/'))
print('github:', set_text('question_35351185003', 'https://github.com/Manish9911'))
pdfs = glob.glob('data/exports/affirm5437/*.pdf')
page.locator('#resume').set_input_files(pdfs[0])
print('resume set')
time.sleep(2)

tasks = [
    ('country', 'United States'),
    ('question_35351180003', 'He/him'),
    ('question_35351181003', 'Yes'),
    ('question_35351182003', 'Yes'),
    ('question_35351183003', 'Tennessee'),
    ('question_35351184003', 'LinkedIn'),
    ('question_35351189003', 'I have not previously'),
    ('4028768003', 'Man'),
    ('4028769003', 'Asian'),
]
for tid, opt in tasks:
    r = pick(tid, opt)
    print(tid, ':', r)
    if 'nomatch' in r:
        ok = page.evaluate(r"""(a) => {
          const lb = document.getElementById('react-select-' + a[0] + '-listbox');
          const o = lb ? [...lb.querySelectorAll('[role=option]')] : [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
          let hit = o.find(x => x.innerText.trim().toLowerCase() === a[1].toLowerCase()) || o[0];
          if (!hit) return 'still no';
          hit.click();
          return 'picked: ' + hit.innerText.trim().slice(0, 45);
        }""", [tid, opt])
        print('  fallback:', ok)
b.close()
