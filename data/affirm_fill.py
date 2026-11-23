import json, time, glob
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "affirm/jobs" in p.url)
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
    ok = page.evaluate(r"""(t) => {
      const o = [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
      let hit = o.find(x => x.innerText.trim().toLowerCase() === t.toLowerCase());
      if (!hit) hit = o.find(x => x.innerText.toLowerCase().includes(t.toLowerCase()));
      if (!hit) return 'no match: ' + o.slice(0,6).map(x => x.innerText.trim()).join('|');
      hit.click();
      return 'picked: ' + hit.innerText.trim().slice(0, 45);
    }""", text)
    time.sleep(0.8)
    return ok

print('first:', set_text('first_name', 'Manish'))
print('last:', set_text('last_name', 'Badugu'))
print('email:', set_text('email', 'badugu.m7@gmail.com'))
print('phone:', set_text('phone', '+1 940-843-6058'))
print('pref:', set_text('question_33220121003', 'Manish'))
print('company:', set_text('question_33220120003', 'Polaris'))
print('linkedin:', set_text('question_33220119003', 'https://www.linkedin.com/in/badugu-manish-2241/'))
print('github:', set_text('question_33220128003', 'https://github.com/Manish9911'))
pdfs = glob.glob('data/exports/affirm/*.pdf')
page.locator('#resume').set_input_files(pdfs[0])
print('resume set')
time.sleep(2)

tasks = [
    ('country', 'United States'),
    ('question_33220123003', 'he/him'),
    ('question_33220124003', 'No'),
    ('question_33220125003', 'Yes'),
    ('question_33220127003', 'No'),
]
for tid, opt in tasks:
    print(tid, ':', pick(tid, opt))
# how learned - text or select?
print('learned:', set_text('question_33220126003', 'Job board'))
b.close()
