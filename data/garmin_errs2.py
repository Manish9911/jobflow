import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(2)
out = f.evaluate(r"""() => {
  const msgs = [];
  document.querySelectorAll(".iCIMS_Message.iCIMS_ErrorMessage").forEach(e => {
    const t = (e.innerText || "").trim();
    if (t && !t.startsWith("By selecting") && !t.includes("Enable Cookies")) msgs.push(t.slice(0, 150));
  });
  // phone fields
  const phone = {
    number: null, type: null,
  };
  document.querySelectorAll("input[name*='PhoneNumber'], select[name*='PhoneType']").forEach(e => {
    if (e.name.includes('PhoneNumber')) phone.number = e.value;
    if (e.name.includes('PhoneType')) phone.type = e.value;
  });
  // consent inputs
  const consent = [...document.querySelectorAll("input[name*='consent'], input[id*='consent']")].map(e => ({name: e.name, id: e.id, type: e.type, checked: e.checked, val: e.value}));
  return {msgs: [...new Set(msgs)], phone: phone, consent: consent};
}""")
print(json.dumps(out, indent=1))
b.close()
