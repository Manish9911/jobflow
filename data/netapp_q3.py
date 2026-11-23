import json, time
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
      if (!forid) return {err: 'no for: ' + labels[0].outerHTML.slice(0, 200)};
      const inp = document.getElementById(forid);
      if (!inp) return {err: 'no input'};
      return {forid, listid: inp.getAttribute('aria-controls'), tag: inp.tagName, type: inp.type};
    }""", [label_re])
    if 'err' in info:
        return info['err']
    print('  field:', info)
    if info['tag'] == 'SELECT':
        r = page.evaluate(r"""(a) => {
          const e = document.getElementById(a[0]);
          const hit = [...e.options].find(o => o.text.trim().toLowerCase() === a[1].toLowerCase());
          if (!hit) return 'no opt: ' + [...e.options].map(o => o.text.trim()).join('|').slice(0, 100);
          const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set;
          s.call(e, hit.value);
          e.dispatchEvent(new Event('change', {bubbles: true}));
          return 'picked: ' + hit.text.trim();
        }""", [info['forid'], option_text])
        time.sleep(1)
        return r
    inp = page.locator('[id="' + info['forid'] + '"]')
    inp.scroll_into_view_if_needed()
    inp.click()
    time.sleep(1.0)
    page.keyboard.type(option_text, delay=50)
    time.sleep(2.0)
    r = page.evaluate(r"""(args) => {
      const ul = document.getElementById(args[0]);
      if (!ul) return 'no list';
      const lis = [...ul.querySelectorAll('li, [role=option]')];
      if (!lis.length) return 'no lis';
      let hit = lis.find(l => l.innerText.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) hit = lis.find(l => l.innerText.toLowerCase().includes(args[1].toLowerCase()));
      if (!hit) return 'no match: ' + lis.map(l => l.innerText.trim()).join(' | ').slice(0, 200);
      hit.click();
      return 'picked: ' + hit.innerText.trim();
    }""", [info['listid'], option_text])
    time.sleep(1.5)
    return r

tasks = [
    ("3\+years of Java backend", "Yes"),
    ("in office a minimum of 3 days", "Yes"),
    ("require employment visa sponsorship", "Yes"),
]
for lab, opt in tasks:
    print(f"{lab} -> {opt}:", pick_by_label(lab, opt))
b.close()
