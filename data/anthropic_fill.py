import json, time, glob
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "anthropic/jobs" in p.url)
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
    page.keyboard.type(text, delay=60)
    time.sleep(1.5)
    opts = page.evaluate(r"""() => {
      const o = [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
      return o.map(x => x.innerText.trim());
    }""")
    if not opts:
        return 'no opts'
    ok = page.evaluate(r"""(t) => {
      const o = [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
      let hit = o.find(x => x.innerText.trim().toLowerCase() === t.toLowerCase());
      if (!hit) hit = o.find(x => x.innerText.toLowerCase().includes(t.toLowerCase()));
      if (!hit) return 'no match: ' + o.slice(0,8).map(x => x.innerText.trim()).join('|');
      hit.click();
      return 'picked: ' + hit.innerText.trim().slice(0, 60);
    }""", text)
    time.sleep(0.8)
    return ok

# --- plain text fields
print('first:', set_text('first_name', 'Manish'))
print('last:', set_text('last_name', 'Badugu'))
print('email:', set_text('email', 'badugu.m7@gmail.com'))
print('phone:', set_text('phone', '+1 940-843-6058'))
print('start:', set_text('question_15797028008', 'Within 30 days'))
print('deadline:', set_text('question_15797029008', 'None'))
print('workaddr:', set_text('question_15797037008', 'Almond Willow CV, Collierville, TN 38017'))
print('linkedin:', set_text('question_15797035008', 'https://www.linkedin.com/in/badugu-manish-2241/'))

# Why Anthropic - humanized, truthful
why = ("I have spent the last four years building and operating backend systems that have to stay fast and reliable under real load, and along the way I became genuinely interested in how machine learning systems get built and deployed, not just consumed. What draws me to Anthropic is that the RL Velocity team sits at that intersection: the actual infrastructure work that decides how quickly researchers can iterate. I like that kind of problem. Removing a bottleneck that shows up in every training run is the kind of leverage I want to work on, and I would rather do it at a company that is trying to build AI systems that stay reliable and steerable as they get more capable. I would be excited to bring my backend and distributed-systems experience to the platform side of that work.")
print('why:', set_text('question_15797031008', why))

# resume
pdfs = glob.glob('data/exports/anthropic/*.pdf')
page.locator('#resume').set_input_files(pdfs[0])
print('resume set:', pdfs[0])
time.sleep(2)

# --- selects
tasks = [
    ('question_15797027008', 'Yes'),
    ('question_15797030008', 'Yes'),
    ('question_15797032008', 'Yes'),
    ('question_15797033008', 'Yes'),
    ('question_15797036008', 'No'),
    ('question_15797038008', 'No'),
    ('question_18372122008', 'I will read'),
    ('question_18374786008', 'I understand and agree'),
    ('gender', 'Male'),
    ('hispanic_ethnicity', 'No'),
    ('veteran_status', 'I am not a protected veteran'),
]
for tid, opt in tasks:
    print(tid, ':', pick(tid, opt))
b.close()
