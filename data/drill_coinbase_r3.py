"""Coinbase 7830 round 3: click exact options, verify twins, submit."""
import sys
from playwright.sync_api import sync_playwright

PICKS = [
    ("candidate-location", "Collierville", "Collierville, Tennessee, United States"),
    ("school--0", "Christian Brothers", "Christian Brothers University"),
    ("degree--0", None, "Master's Degree"),
    ("discipline--0", None, "Computer Science"),
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
        print("PAGE NOT FOUND"); sys.exit(1)
    page.bring_to_front()

    for fid, query, option in PICKS:
        loc = page.locator(f"#{fid}")
        loc.first.click()
        page.wait_for_timeout(300)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(400)
        if query:
            page.keyboard.type(query, delay=40)
            page.wait_for_timeout(1500 if fid == "candidate-location" else 700)
        # click the option
        clicked = page.evaluate("""(opt) => {
            const lbs = [...document.querySelectorAll('[role=listbox], [id$=-listbox]')]
                .filter(l => { const r = l.getBoundingClientRect(); return r.width > 0; });
            for (const lb of lbs) {
                const hit = [...lb.querySelectorAll('[role=option], [class*=option]')]
                    .find(o => o.innerText.trim() === opt);
                if (hit) { hit.click(); return true; }
            }
            return false;
        }""", option)
        print(fid, "->", option, "clicked:", clicked)
        page.wait_for_timeout(800)

    state = page.evaluate("() => [...document.querySelectorAll('input[class*=requiredInput]')].map(t => t.value)")
    print("twins:", state)
    if all(v.strip() for v in state):
        print("ALL SET — submitting")
        page.locator("button:has-text('Submit application')").first.click()
        page.wait_for_timeout(12000)
        body = page.evaluate("() => document.body.innerText")
        print("TAIL:", body.replace("\n\n", " | ")[-800:])
        print("URL:", page.url[:100])
    else:
        print("STILL INCOMPLETE")
