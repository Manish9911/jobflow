import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

name = "5397892_PersonProfileFields.rcf3218"
page.keyboard.type("united states", delay=60)
time.sleep(3)
# read results
res = f.evaluate("""(n) => [...document.getElementById(n + '_dropdown-results').children].map(li => li.textContent.trim()).filter(Boolean)""", name)
print("results:", res)
# click the match
click = f.evaluate("""(args) => {
  const ul = document.getElementById(args[0] + '_dropdown-results');
  const li = [...ul.children].find(x => x.textContent.trim() === args[1]);
  if (!li) return "no li";
  li.click();
  return "clicked " + li.textContent.trim();
}""", [name, "United States"])
print(click)
time.sleep(2)
print("select value:", f.evaluate("(n) => document.getElementById(n).value", name))
print("fake text:", f.evaluate("(n) => document.getElementById(n + '_fakeSelected_icimsDropdown').textContent.trim()", name))
# state select children?
print("state opts:", f.evaluate("(n) => [...document.getElementById(n).options].map(o => o.text).slice(0, 10)", "5397892_PersonProfileFields.rcf3217"))
b.close()
