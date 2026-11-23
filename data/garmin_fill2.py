import json, time, os
import playwright.sync_api as pw

PDF = "C:/Users/badug/jobflow/data/exports/garmin/Manish Badugu Garmin Senior Software Engineer - Mobile iOS.pdf"
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def bysuffix(tag, suffix):
    """find element by name suffix"""
    sel = f"[name$='.Address{suffix}']" if suffix.startswith("Address") else f"[name$='.PersonProfileFields.{suffix}']"
    return f.locator(sel).first

def set_text_suffix(suffix, val):
    return f.evaluate("""(args) => {
      const e = document.querySelector("input[name$='.\" + args[0] + \"']");
      if (!e) return "no el";
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      s.call(e, args[1]);
      e.dispatchEvent(new Event("input", {bubbles: true}));
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "ok";
    }""", [suffix, val])

# 1. file inputs present?
files = f.evaluate(r"""() => [...document.querySelectorAll("input[type=file]")].map(e => ({name: e.name, id: e.id, hidden: e.offsetParent === null}))""")
print("file inputs:", files)

# 2. address via suffix
print("street1:", set_text_suffix("AddressStreet1", "Almond Willow CV"))
print("city:", set_text_suffix("AddressCity", "Collierville"))
print("zip:", set_text_suffix("AddressZip", "38017"))

# 3. state dropdown (ICIMS ajax)
sname_el = f.evaluate(r"""() => { const e = document.querySelector("select[name$='.AddressState']"); return e ? e.id : null; }""")
print("state select id:", sname_el)
if sname_el:
    a = f.locator(f'[id="{sname_el}_icimsDropdown"]')
    a.scroll_into_view_if_needed()
    a.click()
    time.sleep(1.5)
    page.keyboard.type("tennessee", delay=60)
    time.sleep(3)
    pick = f.evaluate("""(args) => {
      const ul = document.querySelector("[id^='" + args[0] + "_dropdown-results'], [id*='_dropdown-results']");
      const res = ul ? [...ul.children].map(x => x.textContent.trim()).filter(Boolean) : null;
      const li = ul ? [...ul.children].find(x => x.textContent.trim() === args[1]) : null;
      if (li) { li.click(); return {opts: res, clicked: "tennessee"}; }
      return {opts: res, clicked: null};
    }""", [sname_el, "Tennessee"])
    print("state pick:", pick)
    time.sleep(1.5)

# 4. verify
out = f.evaluate(r"""() => {
  const g = s => { const e = document.querySelector("input[name$='." + s + "']"); return e ? e.value : null; };
  const ss = document.querySelector("select[name$='.AddressState']");
  return {street1: g("AddressStreet1"), city: g("AddressCity"), zip: g("AddressZip"),
          state: ss ? ss.value : null,
          state_text: ss && ss.options[ss.selectedIndex] ? ss.options[ss.selectedIndex].text : null};
}""")
print("VERIFY:", out)
b.close()
