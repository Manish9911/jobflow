"""Generic Affirm US Greenhouse form filler. Usage: python data/affirm_us_generic.py <job_url> <resume_glob> <role_keywords> <add_skills>
Auto-maps field IDs by label, fills canonical answers, picks EEO, submits."""
import json, re, sys, time, glob, subprocess
import playwright.sync_api as pw

job_url = sys.argv[1]
resume_glob = sys.argv[2]
job_id = job_url.rstrip('/').split('/')[-1]

def set_text(page, id, val):
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

def pick(page, id, text):
    e = page.locator('[id="' + id + '"]')
    e.scroll_into_view_if_needed()
    e.click()
    time.sleep(1.8)
    out = page.evaluate(r"""(a) => {
      const o = [...document.querySelectorAll('.select__option')].filter(x => x.offsetParent !== null);
      let hit = o.find(x => x.innerText.trim().toLowerCase() === a[1].toLowerCase());
      if (!hit) hit = o.find(x => x.innerText.toLowerCase().includes(a[1].toLowerCase()));
      if (!hit) return 'nomatch: ' + o.slice(0, 8).map(x => x.innerText.trim()).join('|');
      hit.click();
      return 'picked: ' + hit.innerText.trim().slice(0, 40);
    }""", [id, text])
    time.sleep(1.0)
    return out

pw = pw_mod = None
from playwright.sync_api import sync_playwright
pw_obj = sync_playwright().start()
b = pw_obj.chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if ('/jobs/' + job_id) in p.url)
time.sleep(3)

# map labels -> ids
mapping = page.evaluate(r"""() => {
  const res = {};
  document.querySelectorAll('label[for]').forEach(l => {
    const t = l.innerText.replace(/\n+/g, ' ').trim();
    if (t) res[t.slice(0, 60)] = l.htmlFor;
  });
  return res;
}""")

def find_id(*subs):
    for label, fid in mapping.items():
        if all(s.lower() in label.lower() for s in subs):
            return fid
    return None

print('first:', set_text(page, 'first_name', 'Manish'))
print('last:', set_text(page, 'last_name', 'Badugu'))
print('email:', set_text(page, 'email', 'badugu.m7@gmail.com'))
print('phone:', set_text(page, 'phone', '+1 940-843-6058'))
pdfs = glob.glob(resume_glob)
if not pdfs:
    print('NO RESUME for', resume_glob)
    sys.exit(1)
# Upload FIRST: Greenhouse re-renders the whole form after file attach,
# wiping any values filled before it.
for _ in range(8):
    n = page.evaluate('() => document.querySelectorAll("input[type=file]").length')
    if n:
        break
    time.sleep(2)
try:
    page.locator('#resume').set_input_files(pdfs[0])
    print('resume set (first):', pdfs[0].split('/')[-1])
except Exception as ex:
    print('resume input not found - form may not have one:', ex)
time.sleep(8)
time.sleep(2)

text_fields = {
    ('linkedin', 'profile'): 'https://www.linkedin.com/in/badugu-manish-2241/',
    ('current company',): 'Polaris',
    ('preferred name',): 'Manish',
    ('github',): 'https://github.com/Manish9911',
}
for subs, val in text_fields.items():
    fid = find_id(*subs)
    if fid:
        print('text ' + str(subs) + ':', set_text(page, fid, val))
    else:
        print('text ' + str(subs) + ': NOT FOUND')

select_tasks = [
    (('pronouns',), 'He/him'),
    (('sponsorship', 'work'), 'Yes'),
    (('sponsorship', 'any point'), 'Yes'),
    (('state or canadian province',), 'Tennessee'),
    (('how did you first learn',), 'LinkedIn'),
    (('previously been employed',), 'I have not previously'),
    (('gender identity',), 'Male'),
    (('race/ethnicity',), 'East Asian'),
    (('gender',), 'Male'),
    (('race',), 'Asian'),
]
for subs, opt in select_tasks:
    fid = find_id(*subs)
    if not fid:
        print('select ' + str(subs) + ': NOT FOUND')
        continue
    r = pick(page, fid, opt)
    print('select ' + str(subs) + ':', r)
    if 'nomatch' in r and fid in ('hispanic_ethnicity', 'veteran_status'):
        pass
# fixed EEO ids (label matcher skips these; always present on Affirm US forms)
for fid, opt in [('gender', 'Male'), ('race', 'Asian'), ('hispanic_ethnicity', 'No'), ('veteran_status', 'Not a protected')]:
    r = page.evaluate(r'''(i) => {
      const e = document.getElementById(i);
      if (!e) return 'no el';
      return 'exists';
    }''', fid)
    if r == 'exists':
        print('select ' + fid + ':', pick(page, fid, opt))

# final retry: any still-empty select gets a second pass by label
for _ in range(2):
    leftover = page.evaluate(r"""() => {
      const res = [];
      document.querySelectorAll('.select__control').forEach(c => {
        if (c.innerText.replace(/\n+/g, ' ').trim() === 'Select...') {
          const shell = c.closest('.select-shell') || c.parentElement.parentElement;
          const lab = shell ? (shell.parentElement || shell).querySelector('label') : null;
          if (lab) res.push({lab: lab.innerText.replace(/\n+/g, ' ').trim().slice(0, 50), id: lab.htmlFor});
        }
      });
      return res;
    }""")
    if not leftover:
        break
    for item in leftover:
        want = 'Asian'
        if re.search(r'gender', item['lab'], re.I):
            want = 'Male'
        elif re.search(r'hispanic|latino', item['lab'], re.I):
            want = 'No'
        elif re.search(r'veteran', item['lab'], re.I):
            want = 'Not a protected'
        elif re.search(r'legally authorized|sponsorship|work in the united states', item['lab'], re.I):
            want = 'Yes'
        print('retry ' + item['lab'] + ':', pick(page, item['id'], want))

# remaining empty selects report
empty = page.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('.select__control').forEach(c => {
    if (c.innerText.replace(/\n+/g, ' ').trim() === 'Select...') {
      const shell = c.closest('.select-shell') || c.parentElement.parentElement;
      const lab = shell ? ((shell.parentElement || shell).querySelector('label') || {innerText: ''}).innerText.replace(/\n+/g, ' ').trim().slice(0, 45) : '';
      res.push(lab);
    }
  });
  return res;
}""")
print('STILL EMPTY:', json.dumps(empty))

if empty:
    print('NOT SUBMITTING - review first')
    pw_obj.stop()
    sys.exit(2)

r = page.evaluate(r"""() => {
  const b = [...document.querySelectorAll('button, input[type=submit]')].filter(e => e.offsetParent !== null && /submit/i.test(e.innerText || e.value || ''))[0];
  if (!b) return 'no submit';
  b.scrollIntoView({block: 'center'});
  b.click();
  return 'clicked';
}""")
print(r)
time.sleep(18)
out = page.evaluate(r"""() => ({
  url: location.href.slice(0, 110),
  body: document.body.innerText.slice(0, 200).replace(/\n+/g, ' | ')
})""")
print(json.dumps(out, indent=1))
pw_obj.stop()
