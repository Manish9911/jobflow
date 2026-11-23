import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def dd_open(name):
    a = f.locator(f'[id="{name}_icimsDropdown"]')
    a.scroll_into_view_if_needed()
    a.click()
    time.sleep(1.5)

def dd_pick(name, text):
    res = f.evaluate("""(n) => [...document.getElementById(n + '_dropdown-results').children].map(li => li.textContent.trim()).filter(Boolean)""", name)
    click = f.evaluate("""(args) => {
      const ul = document.getElementById(args[0] + '_dropdown-results');
      const li = [...ul.children].find(x => x.textContent.trim() === args[1]);
      if (!li) return "no li: " + [...ul.children].map(x => x.textContent.trim()).slice(0, 12).join("|");
      li.click();
      return "clicked " + li.textContent.trim();
    }""", [name, text])
    time.sleep(1.5)
    return res, click

cn = "-2_PersonProfileFields.rcf3218"
dd_open(cn)
page.keyboard.type("united states", delay=60)
time.sleep(3)
print(dd_pick(cn, "United States"))

sn = "-2_PersonProfileFields.rcf3217"
dd_open(sn)
page.keyboard.type("new york", delay=60)
time.sleep(3)
print(dd_pick(sn, "New York"))

# verify both rows
out = f.evaluate("""() => {
  const g = n => { const e = document.getElementById(n); return e ? e.value : null; };
  return {
    r1: {emp: g("5397892_PersonProfileFields.rcf3212"), title: g("5397892_PersonProfileFields.rcf3213"), city: g("5397892_PersonProfileFields.rcf3216"), country: g("5397892_PersonProfileFields.rcf3218"), state: g("5397892_PersonProfileFields.rcf3217"), sm: g("5397892_PersonProfileFields.rcf3214_Month"), sy: g("5397892_PersonProfileFields.rcf3214_Year"), em: g("5397892_PersonProfileFields.rcf3215_Month"), ey: g("5397892_PersonProfileFields.rcf3215_Year")},
    r2: {emp: g("-2_PersonProfileFields.rcf3212"), title: g("-2_PersonProfileFields.rcf3213"), city: g("-2_PersonProfileFields.rcf3216"), country: g("-2_PersonProfileFields.rcf3218"), state: g("-2_PersonProfileFields.rcf3217"), sm: g("-2_PersonProfileFields.rcf3214_Month"), sy: g("-2_PersonProfileFields.rcf3214_Year"), em: g("-2_PersonProfileFields.rcf3215_Month"), ey: g("-2_PersonProfileFields.rcf3215_Year")},
  };
}""")
print(json.dumps(out, indent=1))
b.close()
