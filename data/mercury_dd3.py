import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)

def close_ctnrs():
    f.evaluate(r"""() => { document.activeElement && document.activeElement.blur && document.activeElement.blur(); }""")
    time.sleep(0.4)

def pick_dd(name, query):
    close_ctnrs()
    anchor = f.locator(f"a#{name}_icimsDropdown")
    if anchor.count() == 0:
        return 'no anchor'
    anchor.first.click()
    time.sleep(1.2)
    page.keyboard.type(query, delay=40)
    time.sleep(2.0)
    res = f.locator(f"ul#{name}_dropdown-results li")
    cnt = res.count()
    if cnt == 0:
        txt = f.evaluate(f"""() => {{ const c = document.getElementById('{name}_icimsDropdown_ctnr'); return c ? c.innerText.replace(/\n+/g, ' | ').slice(0,150) : 'no ctnr'; }}""")
        return 'no results: ' + txt
    picked = None
    for i in range(cnt):
        t = res.nth(i).inner_text().strip()
        if t.lower() == query.lower():
            res.nth(i).click()
            picked = t
            break
    if not picked:
        t = res.first.inner_text().strip()
        res.first.click()
        picked = '(first) ' + t
    time.sleep(1)
    return 'picked: ' + picked

def selval(name):
    return f.evaluate(f"""() => {{ const e = document.querySelector(\"select[name='{name}']\"); return e ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : null; }}""")

# education state check
edu = f.evaluate(r"""() => {
  const res = {};
  ['School','Degree','Major','IsGraduated'].forEach(k => {
    const e = document.querySelector("select[name='-1_CandProfileFields." + k + "']");
    res[k] = e ? {val: e.value, text: e.options.length ? (e.options[e.selectedIndex] ? e.options[e.selectedIndex].text : e.value) : e.value, n: e.options.length} : null;
  });
  const os = document.querySelector("input[name='-1_CandProfileFields.OtherSchool']");
  res.OtherSchool = os ? os.value : null;
  return res;
}""")
print('education now:', edu)

print('consent:', pick_dd('rcf3553', 'No'))
print('country:', pick_dd('-1_PersonProfileFields.AddressCountry', 'United States'))
time.sleep(1.5)
print('state:', pick_dd('-1_PersonProfileFields.AddressState', 'Tennessee'))
time.sleep(1)
print('school: already parsed (CBU)')
time.sleep(1)
print('degree:', pick_dd('-1_CandProfileFields.Degree', 'MS'))
time.sleep(1)
print('major:', pick_dd('-1_CandProfileFields.Major', 'Computer'))
time.sleep(1)
print('grad: already Yes')
time.sleep(1)
print('currrole:', pick_dd('-1216622_PersonProfileFields.rcf3269', 'Yes'))
# rcf3049 native
print('source9:', f.evaluate("""() => { const e = document.querySelector("select[name='rcf3049']"); if (!e) return 'no el'; const hit = [...e.options].find(o => /no additional/i.test(o.text)); if (!hit) return 'opts: ' + [...e.options].map(o=>o.text.trim()).join('|'); const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, 'value').set; s.call(e, hit.value); e.dispatchEvent(new Event('change', {bubbles: true})); return 'ok'; }"""))
# verify
for n in ['rcf3553', '-1_PersonProfileFields.AddressCountry', '-1_PersonProfileFields.AddressState', '-1_CandProfileFields.School', '-1_CandProfileFields.Degree', '-1_CandProfileFields.Major', '-1_CandProfileFields.IsGraduated', '-1216622_PersonProfileFields.rcf3269', 'rcf3049']:
    print('VERIFY', n, '=>', selval(n))
b.close()
