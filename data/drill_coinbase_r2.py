"""Coinbase 7830 round 2: menu-driven option clicks for the 4 typeaheads."""
import sys
from playwright.sync_api import sync_playwright

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

    def open_menu(fid):
        loc = page.locator(f"#{fid}")
        loc.first.click()
        page.wait_for_timeout(300)
        page.keyboard.press("ArrowDown")
        page.wait_for_timeout(500)

    def menu_opts():
        return page.evaluate("""() => {
            const lbs = [...document.querySelectorAll('[role=listbox], [id$=-listbox]')]
                .filter(l => { const r = l.getBoundingClientRect(); return r.width > 0; });
            if (!lbs.length) return null;
            return [...lbs[0].querySelectorAll('[role=option], [class*=option]')]
                .map(o => o.innerText.trim()).slice(0, 30);
        }""")

    # 1) degree: open menu, no typing
    open_menu("degree--0")
    opts = menu_opts()
    print("DEGREE options:", opts)
    # 2) discipline: open menu, no typing
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    open_menu("discipline--0")
    opts2 = menu_opts()
    print("DISCIPLINE options:", opts2)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    # 3) location: type, wait for remote
    open_menu("candidate-location")
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)
    loc = page.locator("#candidate-location")
    loc.first.click()
    page.wait_for_timeout(200)
    page.keyboard.press("ArrowDown")
    page.keyboard.type("Collierville", delay=60)
    page.wait_for_timeout(3000)
    opts3 = menu_opts()
    print("LOCATION options after type:", opts3)
    state = page.evaluate("() => [...document.querySelectorAll('input[class*=requiredInput]')].map(t => t.value)")
    print("twins now:", state)
