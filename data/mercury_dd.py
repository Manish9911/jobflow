import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)

def pick_dd(name, query):
    # find the anchor: a#<name>_icimsDropdown (name may contain dots → find by id suffix)
    anchor = f.locator(f"a[id$='{name}_icimsDropdown']")
    n = anchor.count()
    if n == 0:
        # maybe it's a plain select with options already
        return 'no anchor'
    anchor.first.click()
    time.sleep(2)
    # find the search input inside the opened dropdown-container
    search = f.locator(".dropdown-container input[type='text'], .dropdown-container input:not([type])").first
    try:
        search.wait_for(timeout=5000)
    except Exception:
        return 'no search input'
    search.click()
    f.keyboard.type(query, delay=50)
    time.sleep(2.5)
    # results ul
    res = f.locator(f"ul[id$='{name}_dropdown-results'] li")
    cnt = res.count()
    if cnt == 0:
        txt = f.evaluate(r"""() => { const c = document.querySelector('.dropdown-container'); return c ? c.innerText.replace(/\n+/g, ' | ').slice(0,200) : 'no container'; }""")
        return 'no results: ' + txt
    for i in range(cnt):
        t = res.nth(i).inner_text().strip()
        if t.lower() == query.lower() or (query.lower() in t.lower() and i < 5):
            if t.lower() == query.lower() or i == 0:
                res.nth(i).click()
                time.sleep(1)
                return 'picked: ' + t
    # fallback first
    t = res.first.inner_text().strip()
    res.first.click()
    time.sleep(1)
    return 'picked(first): ' + t

# consent
print('consent:', pick_dd('rcf3553', 'I do not consent'))
# current role
print('currrole:', pick_dd('-1_PersonProfileFields.rcf3269', 'Yes'))
# country
print('country:', pick_dd('-1_PersonProfileFields.AddressCountry', 'United States'))
time.sleep(2)
# state
print('state:', pick_dd('-1_PersonProfileFields.AddressState', 'Tennessee'))
time.sleep(1)
# employment state (row 1 Verizon -> New York)
print('empstate:', pick_dd('-1_PersonProfileFields.rcf3217', 'New York'))
b.close()
