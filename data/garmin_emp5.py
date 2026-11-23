import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def set_text(name, val):
    return f.evaluate("""(args) => {
      const e = document.querySelector("input[name='\" + args[0] + \"']");
      if (!e) return "no el";
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      s.call(e, args[1]);
      e.dispatchEvent(new Event("input", {bubbles: true}));
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "ok";
    }""", [name, val])

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

def clear_sel(sid):
    return f.evaluate("""(id) => {
      const e = document.getElementById(id);
      if (!e || e.tagName !== 'SELECT') return "n/a";
      e.value = "0";
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "cleared";
    }""", sid)

R = "5397892_PersonProfileFields."
print("VZ employer:", set_text(R + "rcf3212", "Verizon Communications"))
print("VZ title:", set_text(R + "rcf3213", "Sr. Java Full Stack Developer"))
print("VZ city:", set_text(R + "rcf3216", "New York"))
print("VZ country:", dd_pick(R + "rcf3218", "United States"))
time.sleep(1)
print("VZ state:", dd_pick(R + "rcf3217", "New York"))
print("VZ start:", dd_pick(R + "rcf3214_Month", "Jul", exact=False), set_text(R + "rcf3214_Year", "2025"))
print("VZ end month cleared:", clear_sel(R + "rcf3215_Month"))
print("VZ year end:", set_text(R + "rcf3215_Year", ""))
b.close()
print("PHASE VZ DONE")
