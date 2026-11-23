import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
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

def set_sel_by_text(name, text):
    return f.evaluate("""(args) => {
      const e = document.querySelector("select[name='\" + args[0] + \"']");
      if (!e) return "no el";
      const hit = [...e.options].find(o => o.text.trim().toLowerCase() === args[1].toLowerCase());
      if (!hit) return "no opt: " + [...e.options].map(o => o.text).slice(0, 15).join(",");
      e.value = hit.value;
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return hit.value;
    }""", [name, text])

def clear_sel(name):
    return f.evaluate("""(args) => {
      const e = document.querySelector("select[name='\" + args[0] + \"']");
      if (!e) return "no el";
      e.value = "0";
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "cleared";
    }""", [name])

R1 = "5397892_PersonProfileFields."
R2 = "-2_PersonProfileFields."

# Row 1 -> Equifax (Jul 2024 - Jun 2025)
print("eq employer:", set_text(R1 + "rcf3212", "Equifax"))
print("eq title:", set_text(R1 + "rcf3213", "Full Stack Developer"))
print("eq city:", set_text(R1 + "rcf3216", "Alpharetta"))
print("eq country:", set_sel_by_text(R1 + "rcf3218", "United States"))
time.sleep(1)
print("eq state:", set_sel_by_text(R1 + "rcf3217", "Georgia"))
print("eq start:", set_sel_by_text(R1 + "rcf3214_Month", "Jul"), set_text(R1 + "rcf3214_Year", "2024"))
print("eq end:", set_sel_by_text(R1 + "rcf3215_Month", "Jun"), set_text(R1 + "rcf3215_Year", "2025"))
print("eq reason:", set_ta(R1 + "rcf3268", "Career transition"))

# Row 2 -> Verizon (Jul 2025 - Present)
print("vz employer:", set_text(R2 + "rcf3212", "Verizon Communications"))
print("vz title:", set_text(R2 + "rcf3213", "Sr. Java Full Stack Developer"))
print("vz city:", set_text(R2 + "rcf3216", "New York"))
print("vz country:", set_sel_by_text(R2 + "rcf3218", "United States"))
time.sleep(1)
print("vz state:", set_sel_by_text(R2 + "rcf3217", "New York"))
print("vz start:", set_sel_by_text(R2 + "rcf3214_Month", "Jul"), set_text(R2 + "rcf3214_Year", "2025"))
print("vz end cleared:", clear_sel(R2 + "rcf3215_Month"), set_text(R2 + "rcf3215_Year", ""))
print("vz reason:", set_ta(R2 + "rcf3268", "N/A"))
b.close()
