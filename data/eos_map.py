import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)
btns = page.evaluate(
    """() => {
      const bs = [...document.querySelectorAll("button")].filter(e => (e.innerText||'').trim() === 'Select One' && e.getBoundingClientRect().width > 0);
      return bs.map(e => {
        let blk = e;
        for (let i = 0; i < 8 && blk; i++) {
          const t = (blk.innerText||'').trim();
          if (t.indexOf("?") !== -1 || t.indexOf("ethnicity") !== -1) return {id: e.id, q: t.split(String.fromCharCode(10)).join(" | ").slice(0, 110)};
          blk = blk.parentElement;
        }
        return {id: e.id, q: "??"};
      });
    }"""
)
print(json.dumps(btns, indent=1))
# terms checkbox?
chks = page.evaluate(
    """() => [...document.querySelectorAll("input[type=checkbox]")].map(e => ({id: e.id, checked: e.checked, vis: e.getBoundingClientRect().width > 0}))"""
)
print("checkboxes:", json.dumps(chks))
b.close()
