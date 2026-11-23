"""Coinbase 7830: commit typeahead fields with Enter, verify twins, submit."""
import sys
from playwright.sync_api import sync_playwright

FIELDS = [
    ("candidate-location", "Collierville, TN"),
    ("school--0", "Christian Brothers University"),
    ("degree--0", "Master of Science"),
    ("discipline--0", "Computer and Information Systems"),
]

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9334")
    ctx = browser.contexts[0]
    page = None
    for pg in ctx.pages:
        if "job_app" in pg.url:
            page = pg
            break
    if not page:
        print("PAGE NOT FOUND")
        sys.exit(1)
    page.bring_to_front()

    for fid, val in FIELDS:
        loc = page.locator(f"#{fid}")
        if loc.count() == 0:
            print(fid, "NOT FOUND")
            continue
        loc.first.click()
        page.wait_for_timeout(400)
        # open menu via ArrowDown (react-select)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)
        loc.first.press_sequentially(val, delay=25)
        page.wait_for_timeout(800)
        # list menu options
        opts = page.evaluate("""() => {
            const lbs = [...document.querySelectorAll('[role=listbox], [id$=-listbox]')]
                .filter(l => { const r = l.getBoundingClientRect(); return r.width > 0; });
            return lbs.map(l => [...l.querySelectorAll('[role=option], [class*=option]')]
                .map(o => o.innerText.trim()).slice(0, 10));
        }""")
        print(fid, "menu:", opts)
        page.keyboard.press("Enter")
        page.wait_for_timeout(600)

    page.wait_for_timeout(800)
    state = page.evaluate("""() => {
        const twins = [...document.querySelectorAll('input[class*=requiredInput]')];
        return twins.map(t => t.value);
    }""")
    print("twins:", state)
    if all(v.strip() for v in state):
        print("ALL TWINS SET — clicking submit")
        page.locator("button:has-text('Submit application')").first.click()
        page.wait_for_timeout(10000)
        body = page.evaluate("() => document.body.innerText")
        print("TAIL:", body.replace("\n\n", " | ")[-700:])
        print("URL:", page.url[:100])
