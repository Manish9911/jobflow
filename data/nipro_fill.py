import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "transonic.com/careers" in p.url)

def set_text(name, val):
    return page.evaluate("""(args) => {
      const e = document.querySelector("input[name='\" + args[0] + \"']");
      if (!e) return "no el";
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      s.call(e, args[1]);
      e.dispatchEvent(new Event("input", {bubbles: true}));
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "ok";
    }""", [name, val])

def set_sel(name, text):
    return page.evaluate("""(args) => {
      const e = document.querySelector("select[name='\" + args[0] + \"']");
      if (!e) return "no el";
      const hit = [...e.options].find(o => o.text.trim() === args[1]);
      if (!hit) return "no opt: " + [...e.options].map(o => o.text).join("|");
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLSelectElement.prototype, "value").set;
      s.call(e, hit.value);
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return hit.value;
    }""", [name, text])

print("fn:", set_text("firstname", "Manish"))
print("ln:", set_text("lastname", "Badugu"))
print("em:", set_text("email", "badugu.m7@gmail.com"))
print("ph:", set_text("phone", "+1 940-843-6058"))
print("loc:", set_sel("location", "Ithaca, NY, USA"))
print("pos:", set_sel("choose_position_to_apply_for", "Software Engineer"))

RES = "C:/Users/badug/jobflow/data/exports/nipro/Manish Badugu Nipro Sensing (Transonic) Software Engineer.pdf"
COV = "C:/Users/badug/jobflow/data/exports/nipro/Manish Badugu Nipro Sensing Software Engineer Cover Letter.pdf"
page.set_input_files("input[name='upload_cover_letter']", COV)
page.set_input_files("input[name='upload_resume']", RES)
time.sleep(3)
# verify files attached
chk = page.evaluate(r"""() => {
  const r = document.querySelector("input[name='upload_resume']");
  const c = document.querySelector("input[name='upload_cover_letter']");
  return {resume: r && r.files ? r.files[0].name : null, cover: c && c.files ? c.files[0].name : null};
}""")
print("files:", chk)
b.close()
print("FILL DONE")
