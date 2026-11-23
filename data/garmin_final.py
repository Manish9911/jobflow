import json, time, os
import playwright.sync_api as pw

PDF = "C:/Users/badug/jobflow/data/exports/garmin/" + [f for f in os.listdir("C:/Users/badug/jobflow/data/exports/garmin") if f.endswith(".pdf")][0]
print("PDF:", PDF)

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

events = []
def on_resp(r):
    if r.request.method == "POST":
        events.append({"url": r.request.url[:100], "status": r.status})
page.on("response", on_resp)

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

# 1. Resume upload
f.set_input_files("input[name='PortalProfileFields.Resume_File']", PDF)
time.sleep(8)
print("resume:", f.evaluate("() => { const e = document.querySelector(\"input[name='PortalProfileFields.Resume_FileName']\"); return e ? e.value : null; }"))

# 2. Address -> Collierville TN 38017
for n, v in [("316650_PersonProfileFields.AddressStreet1", "Almond Willow CV"),
             ("316650_PersonProfileFields.AddressCity", "Collierville"),
             ("316650_PersonProfileFields.AddressZip", "38017")]:
    print(n.split(".")[-1], set_text(n, v))
# state: check type
st = f.evaluate("""() => {
  const e = document.querySelector("select[name='316650_PersonProfileFields.AddressState']");
  if (!e) return "none";
  const opts = [...e.options].map(o => o.text);
  return {native: opts.length > 5, sample: opts.slice(0, 6), val: e.value};
}""")
print("state select:", st)
if st and st.get("native"):
    print("state:", f.evaluate("""() => {
      const e = document.querySelector("select[name='316650_PersonProfileFields.AddressState']");
      const hit = [...e.options].find(o => o.text.trim() === "TN" || o.text.trim() === "Tennessee");
      if (!hit) return "no TN opt: " + [...e.options].map(o=>o.text).slice(0,10).join("|");
      e.value = hit.value;
      e.dispatchEvent(new Event("change", {bubbles: true}));
      return "TN=" + hit.value;
    }"""))
b.close()
print("PHASE1 DONE")
