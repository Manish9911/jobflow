import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
R = "5397892_PersonProfileFields."

def set_sel(sid, val):
    return f.evaluate("""(args) => {
      const e = document.getElementById(args[0]);
      if (!e) return "no el";
      e.value = args[1];
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "set " + e.value;
    }""", [sid, val])

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

print("start month:", set_sel(R + "rcf3214_Month", "07"))
print("start year:", set_text(R + "rcf3214_Year", "2025"))
print("end month:", set_sel(R + "rcf3215_Month", "0"))
print("end year:", set_text(R + "rcf3215_Year", ""))

# now find the 'add more' button
btns = f.evaluate(r"""() => [...document.querySelectorAll("input, button, a")].filter(e => (e.value || e.innerText || "").toLowerCase().includes("add more")).map(e => ({tag: e.tagName, name: e.name, t: (e.value || e.innerText || "").trim().slice(0, 50)}))""")
print("add-more buttons:", btns)
b.close()
