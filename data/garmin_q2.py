import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url and "/questions" in p.url)
f = next((ff for ff in page.frames if "in_iframe=1" in ff.url), page.main_frame)

def pick(name, text):
    return f.evaluate("""(args) => {
      const e = document.querySelector("select[name='\" + args[0] + \"']");
      if (!e) return "no el";
      const hit = [...e.options].find(o => o.text.trim() === args[1]);
      if (!hit) return "no opt";
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
      s.call(e, hit.value);
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return hit.value;
    }""", [name, text])

def set_ta(sel, val):
    return f.evaluate("""(args) => {
      const e = document.querySelector(args[0]);
      if (!e) return "no el";
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
      s.call(e, args[1]);
      e.dispatchEvent(new Event("input", {bubbles: true}));
      return "ok";
    }""", [sel, val])

print("source:", pick("rcf3167", "Job Board"))
print("18+:", pick("Q162", "Yes"))
print("work auth:", pick("Q161", "Yes"))
print("h1b transfer:", pick("Q268", "Yes"))
print("on opt:", pick("Q267", "Yes"))
print("salary:", pick("Q214", "$150,000 to $159,999/year"))
print("relocate:", pick("Q154", "No"))
print("onsite days:", pick("Q218", "5"))
print("5 days:", pick("Q266", "Yes"))
print("terminated:", pick("Q167", "No"))

# attestation checkbox
att = f.evaluate(r"""() => {
  const cbs = [...document.querySelectorAll("input[type=checkbox]")].filter(e => e.offsetParent !== null);
  return cbs.map(e => ({name: e.name, id: e.id, checked: e.checked}));
}""")
print("checkboxes:", att)
for cb in att:
    f.evaluate("""(n) => {
      const e = document.querySelector("input[type=checkbox][name='\" + n + \"']") || document.querySelector("input[type=checkbox][id='\" + n + \"']");
      if (e && !e.checked) { e.click(); }
      return e ? e.checked : null;
    }""", cb.get("name") or cb.get("id"))

# interest textarea - find by nearby label text
ints = f.evaluate(r"""() => {
  const tas = [...document.querySelectorAll("textarea")].filter(e => e.offsetParent !== null);
  return tas.map(e => ({name: e.name, ph: e.placeholder, label: (e.closest('tr') || e.closest('div')) ? (e.closest('tr').innerText || e.closest('div').innerText).slice(0, 60) : ''}));
}""")
print("textareas:", ints)
b.close()
print("Q2 FILL DONE")
