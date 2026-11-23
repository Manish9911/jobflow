import json, time, glob
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "chime/jobs" in p.url)
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

def pick(id, sub):
    e = page.locator('[id="' + id + '"]') if id[0].isdigit() else page.locator('#' + id)
    e.scroll_into_view_if_needed()
    e.click()
    time.sleep(1.2)
    page.keyboard.type(sub, delay=40)
    time.sleep(1.8)
    r = page.evaluate(r"""(args) => {
      // find visible option lists
      const lists = [...document.querySelectorAll('[role=listbox] li, [class*=option], [class*=list] li, ul li')].filter(l => l.offsetParent !== null && l.innerText.trim().length > 0 && l.innerText.length < 80);
      if (!lists.length) return 'no opts';
      let hit = lists.find(l => l.innerText.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) hit = lists.find(l => l.innerText.toLowerCase().includes(args[1].toLowerCase()));
      if (!hit) return 'no match: ' + lists.slice(0, 12).map(l => l.innerText.trim()).join(' | ').slice(0, 250);
      hit.click();
      return 'picked: ' + hit.innerText.trim();
    }""", [id, sub])
    time.sleep(1.0)
    return r

# plain text fields
print('first:', set_text('first_name', 'Manish'))
print('last:', set_text('last_name', 'Badugu'))
print('pref:', set_text('preferred_name', 'Manish'))
print('email:', set_text('email', 'badugu.m7@gmail.com'))
print('phone:', set_text('phone', '+1 940-843-6058'))
print('linkedin:', set_text('question_38831374002', 'https://www.linkedin.com/in/badugu-manish-2241/'))
print('heard:', set_text('question_38831375002', 'Company career site'))

# resume file
pdfs = glob.glob('data/exports/chime/*.pdf')
print('pdfs:', pdfs)
if pdfs:
    page.locator('#resume').set_input_files(pdfs[0])
    print('resume set')
time.sleep(2)

# selects (click + type + pick)
tasks = [
    ('country', 'United States'),
    ('question_38831376002', 'United States'),
    ('question_38831377002', 'Yes'),
    ('question_38831378002', 'Yes'),
    ('question_38831379002', 'Yes'),
    ('question_38831380002', 'No'),
    ('4024620002', 'Male'),
    ('4024621002', 'Asian'),
    ('4024622002', 'Straight'),
    ('4024623002', 'No'),
    ('4024624002', 'No'),
]
for tid, opt in tasks:
    print(tid, '->', opt, ':', pick(tid, opt))
b.close()
