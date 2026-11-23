import time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

def fill(id, text):
    page.evaluate("""(a) => {
      const e = document.getElementById(a.id);
      if (!e) throw new Error("missing " + a.id);
      e.scrollIntoView({block: "center"});
      e.focus();
      const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
      setter.call(e, a.val);
      e.dispatchEvent(new Event("input", {bubbles: true}));
      e.dispatchEvent(new Event("change", {bubbles: true}));
    }""", {"id": id, "val": text})
    time.sleep(0.3)

fill("selfIdentifiedDisabilityData--name", "Manish Badugu")
fill("selfIdentifiedDisabilityData--dateSignedOn-dateSectionMonth-input", "11")
fill("selfIdentifiedDisabilityData--dateSignedOn-dateSectionDay-input", "18")
fill("selfIdentifiedDisabilityData--dateSignedOn-dateSectionYear-input", "2026")

# verify labels before clicking
labels = page.evaluate(
    """() => {
      const ids = ["64cbff5f364f10000ae7a421cf210000", "64cbff5f364f10000aeec521b4ec0000", "64cbff5f364f10000af3af293a050000"];
      return ids.map(id => {
        const e = document.getElementById(id + "-disabilityStatus");
        let lab = "";
        const l = document.querySelector('label[for="' + id + '-disabilityStatus"]');
        if (l) lab = (l.innerText||"").trim();
        if (!lab && e && e.closest("li")) lab = (e.closest("li").innerText||"").trim();
        return {id, label: lab.slice(0, 80)};
      });
    }"""
)
print(json.dumps(labels, indent=1))
no_box = "64cbff5f364f10000aeec521b4ec0000"
if not any("No, I do not have" in (l["label"] or "") for l in labels if l["id"] == no_box):
    print("SAFETY: label mismatch, not clicking")
else:
    page.evaluate("""(id) => {
      const e = document.getElementById(id + "-disabilityStatus");
      e.scrollIntoView({block: "center"});
      e.click();
    }""", no_box)
    time.sleep(0.5)
st = page.evaluate("""() => {
  const ids = ["64cbff5f364f10000ae7a421cf210000", "64cbff5f364f10000aeec521b4ec0000", "64cbff5f364f10000af3af293a050000"];
  return ids.map(id => document.getElementById(id + "-disabilityStatus").checked);
}""")
print("boxes:", st)
vals = page.evaluate("""() => {
  const g = id => { const e = document.getElementById(id); return e ? e.value : "?"; };
  return {name: g("selfIdentifiedDisabilityData--name"), m: g("selfIdentifiedDisabilityData--dateSignedOn-dateSectionMonth-input"), d: g("selfIdentifiedDisabilityData--dateSignedOn-dateSectionDay-input"), y: g("selfIdentifiedDisabilityData--dateSignedOn-dateSectionYear-input")};
}""")
print("fields:", vals)
b.close()
