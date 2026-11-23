"""Figma 5853: commit the three multi-selects via Playwright.
Click control -> click exact option in the visible menu (may need reopen)."""
import asyncio
from playwright.async_api import async_playwright

JOBS = [
    ("question_19016795004[]", ["Product-facing Full Stack"]),
    ("question_14492722004[]", ["Full-Stack", "Backend"]),
    ("question_14492723004[]", ["Java", "JavaScript/TypeScript"]),
]

async def pick(page, fid, want):
    el = page.locator("#" + fid.replace("[", "\\[").replace("]", "\\]") if False else "#css-f42aui")  # placeholder
    # use the raw id via evaluate-based click instead
    await page.evaluate("""(fid) => {
        const el = document.getElementById(fid);
        el.scrollIntoView({block: 'center'});
    }""", fid)
    await asyncio.sleep(0.3)
    for attempt in range(2):
        # open menu via mouse click on the input
        await page.evaluate("""(fid) => {
            const el = document.getElementById(fid);
            const r = el.getBoundingClientRect();
            // dispatch a real click on the control
            const ctrl = el.closest('.select__control') || el;
            ctrl.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
            ctrl.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
            ctrl.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        }""", fid)
        await asyncio.sleep(1.2)
        # visible options in an open menu
        menu = page.locator(".select__menu:visible")
        if await menu.count() == 0:
            # try keyboard: focus + ArrowDown to open
            await page.evaluate("""(fid) => document.getElementById(fid).focus()""", fid)
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(1.0)
            menu = page.locator(".select__menu:visible")
        if await menu.count() == 0:
            continue
        # click the wanted option
        ok = await menu.evaluate("""(m, want) => {
            const opts = [...m.querySelectorAll('[role=option]')];
            const o = opts.find(x => x.textContent.trim() === want);
            if (!o) return null;
            o.click();
            return true;
        }""", want)
        if ok:
            await asyncio.sleep(0.8)
            return "OK"
        # option not found - report
        labels = await menu.evaluate("""(m) => [...m.querySelectorAll('[role=option]')]
            .map(x => x.textContent.trim()).slice(0, 12)""")
        return "NO OPT: " + str(labels)
    return "MENU WONT OPEN"

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
        for fid, wants in JOBS:
            for w in wants:
                r = await pick(page, fid, w)
                print(fid, "|", w, "->", r)
            await asyncio.sleep(0.5)
        # verify via DOM: count selected value labels in each control
        st = await page.evaluate("""() => {
            const out = {};
            for (const fid of ['question_19016795004[]', 'question_14492722004[]', 'question_14492723004[]']) {
                const el = document.getElementById(fid);
                const ctrl = el.closest('.select__control') || el.parentElement;
                out[fid] = (ctrl.textContent || '').trim().slice(0, 120);
            }
            return out;
        }""")
        print("final:", st)

asyncio.run(main())
