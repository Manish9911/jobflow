"""Figma 5853 candidate-location typeahead via Playwright (CDP 9334).
Proven Greenhouse NEW-embed recipe: type into visible input, click exact
option in the visible listbox. Enter does NOT commit."""
import asyncio
from playwright.async_api import async_playwright

WANT = "Collierville, Tennessee, United States"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9334")
        ctx = browser.contexts[0]
        page = None
        for pg in ctx.pages:
            if "figma" in (pg.url or "") and "greenhouse" in (pg.url or ""):
                page = pg
                break
        if page is None:
            print("NO PAGE")
            return
        await page.bring_to_front()
        el = page.locator("#candidate-location")
        await el.scroll_into_view_if_needed()
        await el.click()
        await asyncio.sleep(0.5)
        # clear via keyboard (React-safe)
        await el.press("Control+a")
        await el.press("Delete")
        await asyncio.sleep(0.4)
        await el.type("Collierville", delay=120)
        await asyncio.sleep(2.5)
        # dump what appeared
        dump = await page.evaluate("""() => {
            const visible = x => {
                const r = x.getBoundingClientRect();
                return r.height > 4 && r.top >= 0 && r.top < window.innerHeight;
            };
            const all = [...document.querySelectorAll('*')]
                .filter(visible)
                .filter(x => /collierville/i.test(x.textContent || '') && (x.textContent||'').length < 120)
                .map(x => x.tagName + '.' + String(x.className || '').slice(0, 40) + ' role=' + (x.getAttribute('role') || '-') + ' id=' + (x.id || '') + ' :: ' + (x.textContent || '').trim().slice(0, 70));
            return all.slice(0, 15);
        }""")
        print("appeared:", dump)
        # try generic option selectors
        for sel in ["[role=option]", "[id*=listbox] [id*=option]", ".select__menu-list li", "[class*=suggestion]", "[class*=autocomplete] li"]:
            loc = page.locator(sel)
            n = await loc.count()
            if n:
                labels = []
                for i in range(min(n, 8)):
                    labels.append((await loc.nth(i).inner_text()).strip()[:70])
                print("sel", sel, "->", labels)
        print("DONE-DUMP")
        await asyncio.sleep(0.2)
        return

asyncio.run(main())
