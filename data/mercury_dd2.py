import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)

def close_ctnrs():
    f.evaluate(r"""() => { document.querySelectorAll('.dropdown-invisible').forEach(i => i.blur()); document.body.click(); }""")
    time.sleep(0.5)

def pick_dd(name, query):
    close_ctnrs()
    anchor = f.locator(f"a#{name}_icimsDropdown")
    if anchor.count() == 0:
        return 'no anchor'
    anchor.first.click()
    time.sleep(1.5)
    ctnr = f.locator(f"#{name}_icimsDropdown_ctnr")
    search = ctnr.locator("input.dropdown-search").first
    try:
        search.wait_for(state="visible", timeout=5000)
    except Exception:
        # maybe hidden until focus
        search.click(force=True)
    search.click()
    search.fill("")
    f.keyboard.type(query, delay=40)
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

# verify current visible state of emp rows first
rows = f.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('input[name*="rcf3212"]').forEach(e => {
    const tr = e.closest('tr') || e.closest('div');
    res.push({name: e.name, val: e.value, vis: e.offsetParent !== null});
  });
  return res;
}""")
print('emp rows:', rows)

print('consent:', pick_dd('rcf3553', 'No'))
print('country:', pick_dd('-1_PersonProfileFields.AddressCountry', 'United States'))
time.sleep(1.5)
print('state:', pick_dd('-1_PersonProfileFields.AddressState', 'Tennessee'))
b.close()
