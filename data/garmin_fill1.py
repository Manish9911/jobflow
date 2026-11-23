import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
page.bring_to_front()
time.sleep(1)

# 1. Resume upload
pdf = r"C:\Users\badug\jobflow\data\exports\garmin\Manish Badugu Garmin Senior Software Engineer - Mobile iOS.pdf"
f.set_input_files("input[name='PortalProfileFields.Resume_File']", pdf)
time.sleep(3)
fn = f.evaluate("() => document.querySelector(\"input[name='PortalProfileFields.Resume_FileName']\").value")
print("resume file:", fn)

# 2. Address
def set_select(name, text):
    return f.evaluate("""(args) => {
      const sel = document.querySelector("select[name='\" + args[0] + \"']");
      if (!sel) return "no sel";
      const opts = [...sel.options];
      const hit = opts.find(o => o.text.trim().toLowerCase() === args[1].toLowerCase() || o.text.trim().toLowerCase().startsWith(args[1].toLowerCase()));
      if (hit) { sel.value = hit.value; sel.dispatchEvent(new Event('change', {bubbles: true})); return hit.value; }
      const o = document.createElement('option');
      o.value = args[1]; o.text = args[1];
      sel.appendChild(o); sel.value = args[1];
      sel.dispatchEvent(new Event('change', {bubbles: true}));
      return "created:" + args[1];
    }""", [name, text])

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

print("state:", set_select("316650_PersonProfileFields.AddressState", "Tennessee"))
print("street1:", set_select("316650_PersonProfileFields.AddressStreet1", "Almond Willow CV"))
print("city:", set_text("316650_PersonProfileFields.AddressCity", "Collierville"))
print("zip:", set_text("316650_PersonProfileFields.AddressZip", "38017"))

# 3. How did you hear
print("board:", set_select("rcf3049", "Other Job Board"))
print("boardtext:", set_text("rcf3049_Text", "hiring.cafe"))

# 4. Education state
print("edu state:", set_select("491964_CandProfileFields.EducationState", "Tennessee"))

b.close()
