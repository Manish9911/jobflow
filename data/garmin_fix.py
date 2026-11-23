import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def set_sel(sid, val):
    return f.evaluate("""(args) => {
      const e = document.getElementById(args[0]);
      if (!e) return "no el";
      e.value = args[1];
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "set " + e.value;
    }""", [sid, val])

def set_ta(name, val):
    return f.evaluate("""(args) => {
      const e = document.querySelector("textarea[name='\" + args[0] + \"']");
      if (!e) return "no el";
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
      s.call(e, args[1]);
      e.dispatchEvent(new Event("input", {bubbles: true}));
      return "ok";
    }""", [name, val])

def dd_pick(sid, text, exact=True):
    a = f.locator(f'[id="{sid}_icimsDropdown"]')
    a.scroll_into_view_if_needed()
    a.click()
    time.sleep(1.2)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    time.sleep(0.4)
    page.keyboard.type(text, delay=50)
    time.sleep(3)
    res = f.evaluate("""(args) => {
      const ul = document.getElementById(args[0] + '_dropdown-results');
      if (!ul) return {opts: null};
      const opts = [...ul.children].map(x => x.textContent.trim()).filter(Boolean);
      const li = [...ul.children].find(x => args[2] ? x.textContent.trim() === args[1] : x.textContent.trim().toLowerCase().startsWith(args[1].toLowerCase()));
      if (li) { li.click(); return {opts: opts, clicked: li.textContent.trim()}; }
      return {opts: opts, clicked: null};
    }""", [sid, text, exact])
    time.sleep(1.2)
    return res

# 1. Verizon: end date fully blank (day=0)
print("VZ end day:", set_sel("5397892_PersonProfileFields.rcf3215_Date", "0"))
# 2. Verizon: reason = N/A
print("VZ reason:", set_ta("5397892_PersonProfileFields.rcf3268", "N/A"))
# 3. Equifax: start day = 1, end day = 1
print("EQ start day:", set_sel("-2_PersonProfileFields.rcf3214_Date", "1"))
print("EQ end day:", set_sel("-2_PersonProfileFields.rcf3215_Date", "1"))
# 4. Education state = Tennessee
print("EDU state:", dd_pick("491964_CandProfileFields.EducationState", "Tennessee"))
b.close()
print("FIXES DONE")
