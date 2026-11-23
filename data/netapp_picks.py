import json, time, re as re2
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

def pick_by_label(label_re, option_text):
    info = page.evaluate(r"""(args) => {
      const re = new RegExp(args[0], 'i');
      const labels = [...document.querySelectorAll('label')].filter(l => re.test((l.innerText || '').trim()));
      if (!labels.length) return {err: 'no label'};
      const forid = labels[0].getAttribute('for');
      if (!forid) return {err: 'no for'};
      const inp = document.getElementById(forid);
      if (!inp) return {err: 'no input'};
      const listid = inp.getAttribute('aria-controls');
      return {forid, listid, label: (labels[0].innerText || '').trim().slice(0, 60)};
    }""", [label_re])
    if 'err' in info:
        return info['err']
    inp = page.locator('[id="' + info['forid'] + '"]')
    inp.scroll_into_view_if_needed()
    inp.click()
    time.sleep(1.0)
    page.keyboard.type(option_text, delay=50)
    time.sleep(2.0)
    # find listbox and click matching option
    r = page.evaluate(r"""(args) => {
      const ul = document.getElementById(args[0]);
      if (!ul) return 'no list ' + args[0];
      const lis = [...ul.querySelectorAll('li, [role=option]')];
      if (!lis.length) return 'no lis';
      const texts = lis.map(l => l.innerText.trim());
      let hit = lis.find(l => l.innerText.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) hit = lis.find(l => l.innerText.toLowerCase().includes(args[1].toLowerCase()));
      if (!hit) return 'no match: ' + texts.join(' | ').slice(0, 200);
      hit.click();
      time = null;
      return 'picked: ' + hit.innerText.trim();
    }""", [info['listid'], option_text])
    time.sleep(1.5)
    # verify
    v = page.evaluate(r"""(id) => { const e = document.getElementById(id); return e ? (e.value || e.getAttribute('title') || '') : null; }""", info['forid'])
    return f"{r} [verify: {v}]"

tasks = [
    ("sponsorship for employment", "Yes"),
    ("Highest Level of Education", "Master"),
    ("Gender", "Male"),
    ("Ethnicity", "Asian"),
    ("Veteran Status", "No"),
    ("military spouse", "No"),
    ("associated with NetApp", "No"),
    ("restrictive covenants", "No"),
    ("Disability Status", "No"),
]
for lab, opt in tasks:
    print(f"{lab} -> {opt}:", pick_by_label(lab, opt))
b.close()
