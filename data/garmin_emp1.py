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

def set_sel(name, val):
    return f.evaluate("""(args) => {
      const e = document.querySelector("select[name='\" + args[0] + \"']");
      if (!e) return "no el";
      e.value = args[1];
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return e.value;
    }""", [name, val])

P = "5397892_PersonProfileFields."
print("employer:", set_text(P + "rcf3212", "Polaris"))
print("title:", set_text(P + "rcf3213", "Software Developer"))
print("start month:", set_sel(P + "rcf3214_Month", "06"))
print("start year:", set_text(P + "rcf3214_Year", "2021"))
print("end month:", set_sel(P + "rcf3215_Month", "11"))
print("end year:", set_text(P + "rcf3215_Year", "2022"))
print("reason:", set_ta(P + "rcf3268", "Career transition"))

# find Add More (Employment) button
btn = f.evaluate("""() => {
  const b = [...document.querySelectorAll("a, button, input")].find(x => /add more/i.test((x.innerText || x.value || "")) && /employ/i.test((x.innerText || x.value || "")));
  return b ? (x = b, {tag: b.tagName, val: (b.innerText || b.value || "").slice(0, 50)}) : null;
}""")
print("add more btn:", btn)
b.close()
