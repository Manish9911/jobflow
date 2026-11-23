import time, json
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "highroller-careers.com" in p.url)
d = page.evaluate(
    """() => {
      const radios = [...document.querySelectorAll("input[type=radio]")];
      return radios.map(r => {
        const blk = r.closest("fieldset, div");
        return {id: r.id, value: r.value, label: blk ? (blk.innerText||"").trim().replace(/\s+/g," ").slice(0,160) : ""};
      });
    }"""
)
print(json.dumps(d, indent=1))
b.close()
