import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

sid = "316650_PersonProfileFields.AddressStreet1"
a = f.locator(f'[id="{sid}_icimsDropdown"]')
a.scroll_into_view_if_needed()
a.click()
time.sleep(1.2)
page.keyboard.type("Almond", delay=60)
time.sleep(2.5)
# click "— Enter Manually —"
click = f.evaluate("""(id) => {
  const ul = document.getElementById(id + '_dropdown-results');
  const li = [...ul.children].find(x => x.textContent.trim() === '— Enter Manually —');
  if (!li) return "no manual opt";
  li.click();
  return "clicked manual";
}""", sid)
print(click)
time.sleep(1)
# after manual mode, the typed text should remain in the search box; type full street if empty
val = f.evaluate("(id) => document.getElementById(id).value", sid)
print("value after manual:", repr(val))
if not val or val.strip() == "":
    f.locator(f'[id="{sid}_icimsDropdown"]').click()
    time.sleep(1)
    page.keyboard.type("Almond Willow CV", delay=60)
    time.sleep(2)
    # blur to commit
    f.evaluate("(id) => { const s = document.getElementById(id); s.blur(); s.dispatchEvent(new Event('change', {bubbles:true})); }", sid)
    time.sleep(1)
val = f.evaluate("(id) => document.getElementById(id).value", sid)
print("final street1:", repr(val))
b.close()
