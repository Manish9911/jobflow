import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def dd_select(sid, text, exact=False):
    a = f.locator(f'[id="{sid}_icimsDropdown"]')
    a.scroll_into_view_if_needed()
    a.click()
    time.sleep(1.2)
    # clear existing text
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    time.sleep(0.5)
    page.keyboard.type(text, delay=50)
    time.sleep(3)
    opts = f.evaluate("""(id) => {
      const ul = document.getElementById(id + '_dropdown-results');
      return ul ? [...ul.children].map(x => x.textContent.trim()).filter(Boolean) : null;
    }""", sid)
    print("  opts:", opts)
    click = f.evaluate("""(args) => {
      const ul = document.getElementById(args[0] + '_dropdown-results');
      if (!ul) return "no ul";
      const li = [...ul.children].find(x => (args[2] ? x.textContent.trim() === args[1] : x.textContent.trim().toLowerCase().startsWith(args[1].toLowerCase())));
      if (!li) return "no li";
      li.click();
      return "clicked: " + li.textContent.trim();
    }""", [sid, text, exact])
    print(" ", click)
    time.sleep(1.5)
    val = f.evaluate("(id) => document.getElementById(id).value", sid)
    print("  value:", repr(val))

print("STREET1:")
dd_select("316650_PersonProfileFields.AddressStreet1", "Almond Willow CV", exact=True)
print("STATE:")
dd_select("316650_PersonProfileFields.AddressState", "Tennessee", exact=True)
b.close()
