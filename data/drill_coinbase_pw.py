"""Coinbase 7830 Greenhouse: fill 4 text fields via Playwright (trusted events) + submit."""
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
    print("page:", page.url[:80])

    for fid, val in FIELDS:
        loc = page.locator(f"#{fid}")
        if loc.count() == 0:
            print(fid, "NOT FOUND")
            continue
        loc.first.click()
        loc.first.press("Control+a")
        loc.first.press("Delete")
        loc.first.type(val, delay=30)
        print(fid, "typed")

    page.wait_for_timeout(1200)
    state = page.evaluate("""() => {
        const twins = [...document.querySelectorAll('input[class*=requiredInput]')];
        return twins.map(t => t.value);
    }""")
    print("twins after typing:", state)

    if all(v.strip() for v in state):
        print("CLICKING SUBMIT")
        page.locator("button:has-text('Submit application')").first.click()
        page.wait_for_timeout(8000)
        body = page.evaluate("() => document.body.innerText")
        tail = body.replace("\n\n", " | ")
        print("TAIL:", tail[-600:])
        print("URL:", page.url[:100])
    else:
        print("SUBMIT SKIPPED: twins still empty")
