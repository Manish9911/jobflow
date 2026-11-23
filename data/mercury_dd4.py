import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)

def pick_dd(name, query):
    f.evaluate(r"""() => { const a = document.activeElement; if (a && a.blur) a.blur(); }""")
    time.sleep(0.4)
    anchor = f.locator(f"a#{name}_icimsDropdown")
    if anchor.count() == 0:
        return 'no anchor'
    anchor.first.click()
    time.sleep(1.0)
    # focus the search input via JS
    fok = f.evaluate(f"""() => {{ const i = document.querySelector("#{name}_icimsDropdown_ctnr input.dropdown-search"); if (!i) return 'no input'; i.focus(); return 'focused'; }}""")
    if fok != 'focused':
        return fok
    time.sleep(0.5)
    page.keyboard.type(query, delay=40)
    time.sleep(2.0)
    # find + JS-click the matching li
    out = f.evaluate(f"""(q) => {{
      const ul = document.querySelector('ul#{name}_dropdown-results');
      if (!ul) return 'no ul';
      const lis = [...ul.querySelectorAll('li')];
      if (!lis.length) return 'no lis: ' + ul.innerText.replace(/\n+/g, ' | ').slice(0,120);
      let hit = lis.find(li => li.innerText.trim().toLowerCase() === q.toLowerCase());
      if (!hit) hit = lis.find(li => li.innerText.toLowerCase().includes(q.toLowerCase()));
      if (!hit) return 'no match: ' + lis.map(l => l.innerText.trim()).join(' | ').slice(0,150);
      hit.click();
      return 'clicked: ' + hit.innerText.trim();
    }}""", query)
    time.sleep(1.0)
    return out

def selval(name):
    return f.evaluate(f"""() => {{ const e = document.querySelector(\"select[name='{name}']\"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; }}""")

print('consent:', pick_dd('rcf3553', 'No'))
print('country:', pick_dd('-1_PersonProfileFields.AddressCountry', 'United States'))
time.sleep(1.5)
print('state:', pick_dd('-1_PersonProfileFields.AddressState', 'Tennessee'))
time.sleep(1)
print('degree:', pick_dd('-1_CandProfileFields.Degree', 'MS'))
time.sleep(1)
print('major:', pick_dd('-1_CandProfileFields.Major', 'Computer'))
time.sleep(1)
print('currrole:', pick_dd('-1216622_PersonProfileFields.rcf3269', 'Yes'))
print('source9:', f.evaluate("""() => { const e = document.querySelector("select[name='rcf3049']"); if (!e) return 'no el'; const hit = [...e.options].find(o => /no additional/i.test(o.text)); if (!hit) return 'opts: ' + [...e.options].map(o=>o.text.trim()).join('|'); const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set; s.call(e, hit.value); e.dispatchEvent(new Event('change', {bubbles: true})); return 'ok'; }"""))
for n in ['rcf3553', '-1_PersonProfileFields.AddressCountry', '-1_PersonProfileFields.AddressState', '-1_CandProfileFields.School', '-1_CandProfileFields.Degree', '-1_CandProfileFields.Major', '-1_CandProfileFields.IsGraduated', '-1216622_PersonProfileFields.rcf3269', 'rcf3049']:
    print('VERIFY', n, '=>', selval(n))
b.close()
