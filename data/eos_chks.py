import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

chks = page.evaluate(
    """() => [...document.querySelectorAll("input[type=checkbox]")].map(e => {
      const r = e.getBoundingClientRect();
      let label = "";
      const lab = document.querySelector('label[for="' + e.id + '"]');
      if (lab) label = (lab.innerText||"").trim().slice(0, 80);
      return {id: e.id, checked: e.checked, vis: r.width > 0, label};
    })"""
)
print(json.dumps(chks, indent=1))
for c in chks:
    if not c["checked"] and c["vis"]:
        page.evaluate("id => { const e = document.getElementById(id); if (e) e.click(); }", c["id"])
        time.sleep(0.4)
after = page.evaluate(
    """() => [...document.querySelectorAll("input[type=checkbox]")].map(e => e.id + "=" + e.checked)"""
)
print("after:", after)
b.close()
