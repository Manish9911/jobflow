"""Figma 5853 candidate-location: click Tennessee option (menu is open)."""
import asyncio
from playwright.async_api import async_playwright

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
        # if menu closed, reopen
        n = await page.locator("#react-select-candidate-location-option-0").count()
        vis = n and await page.locator("#react-select-candidate-location-option-0").is_visible()
        if not vis:
            el = page.locator("#candidate-location")
            await el.scroll_into_view_if_needed()
            await el.click()
            await asyncio.sleep(0.4)
            await el.press("Control+a")
            await el.press("Delete")
            await asyncio.sleep(0.3)
            await el.type("Collierville", delay=120)
            await asyncio.sleep(2.5)
        # find the Tennessee option by text
        box = page.locator("#react-select-candidate-location-listbox, .select__menu-list")
        n = await box.locator("[role=option]").count()
        target = None
        for i in range(n):
            t = (await box.locator("[role=option]").nth(i).inner_text()).strip()
            if "Tennessee" in t:
                target = i
                break
        if target is None:
            print("NO TENNESSEE OPTION of", n)
            return
        opt = box.locator("[role=option]").nth(target)
        label = (await opt.inner_text()).strip()
        print("clicking:", label)
        await opt.click()
        await asyncio.sleep(1.5)
        st = await page.evaluate("""() => {
            const tw = [...document.querySelectorAll('input')].filter(i => /requiredInput/.test(i.className || ''));
            const chip = document.querySelector('#candidate-location .select__value-container, [id*=candidate-location] [class*=value-container]');
            return {
                visible: document.getElementById('candidate-location').value,
                chip: chip ? chip.textContent.trim() : null,
                twins: tw.map(i => i.value).slice(0, 8),
            };
        }""")
        print("state:", st)

asyncio.run(main())
