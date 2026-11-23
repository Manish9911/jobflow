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

def dd_pick(sid, text, exact=True):
    a = f.locator(f'[id="{sid}_icimsDropdown"]')
    a.scroll_into_view_if_needed()
    a.click()
    time.sleep(1.2)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    time.sleep(0.4)
    page.keyboard.type(text, delay=40)
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

print("eq start:", set_sel("-2_PersonProfileFields.rcf3214_Month", "07"), set_sel("-2_PersonProfileFields.rcf3214_Date", "1"), set_sel("-2_PersonProfileFields.rcf3214_Year", "2024") if False else "")
# year is an input, not select
yr = f.evaluate("""(args) => {
  const e = document.getElementById(args[0]);
  if (!e) return "no el";
  const proto = e.tagName === 'INPUT' ? window.HTMLInputElement.prototype : window.HTMLSelectElement.prototype;
  const s = Object.getOwnPropertyDescriptor(proto, 'value').set;
  s.call(e, args[1]);
  e.dispatchEvent(new Event("input", {bubbles: true}));
  e.dispatchEvent(new Event("change", {bubbles: true}));
  return "set " + e.value;
}""", ["-2_PersonProfileFields.rcf3214_Year", "2024"])
print("eq start year:", yr)
print("eq end:", set_sel("-2_PersonProfileFields.rcf3215_Month", "06"), set_sel("-2_PersonProfileFields.rcf3215_Date", "1"))
yr2 = f.evaluate("""(args) => {
  const e = document.getElementById(args[0]);
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  s.call(e, args[1]);
  e.dispatchEvent(new Event("input", {bubbles: true}));
  e.dispatchEvent(new Event("change", {bubbles: true}));
  return "set " + e.value;
}""", ["-2_PersonProfileFields.rcf3215_Year", "2025"])
print("eq end year:", yr2)

# consent: "I do not consent to receive text messages"
print("consent:", dd_pick("rcf3553", "I do not consent to receive text messages"))
b.close()
print("FIX2 DONE")
