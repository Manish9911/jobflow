import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)

def set_text(name, val):
    return f.evaluate("""(a) => {
      const e = document.querySelector("input[name='" + a[0] + "']");
      if (!e) return 'no el';
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [name, val])

print('street:', set_text('-1_PersonProfileFields.AddressStreet1', 'Almond Willow CV'))
time.sleep(0.5)
print('city:', set_text('-1_PersonProfileFields.AddressCity', 'Collierville'))
time.sleep(0.5)
print('zip:', set_text('-1_PersonProfileFields.AddressZip', '38017'))
time.sleep(1.0)
# re-set resume file
fi = f.query_selector("input[type='file']")
print('file input:', bool(fi))
if fi:
    fi.set_input_files("C:/Users/badug/jobflow/data/exports/mercury/Manish Badugu Mercury Insurance Senior Software Engineer.pdf")
    time.sleep(3)
# verify
v = f.evaluate(r"""() => {
  const t = (n) => { const e = document.querySelector("input[name='" + n + "']"); return e ? e.value : null; };
  const fi = document.querySelector("input[type='file']");
  return {
    street: t('-1_PersonProfileFields.AddressStreet1'),
    city: t('-1_PersonProfileFields.AddressCity'),
    zip: t('-1_PersonProfileFields.AddressZip'),
    state: (() => { const e = document.querySelector("select[name='-1_PersonProfileFields.AddressState']"); return e ? e.options[e.selectedIndex].text : null; })(),
    country: (() => { const e = document.querySelector("select[name='-1_PersonProfileFields.AddressCountry']"); return e ? e.options[e.selectedIndex].text : null; })(),
    resume: fi && fi.files && fi.files.length ? fi.files[0].name : null,
  };
}""")
print(json.dumps(v, indent=1))
b.close()
