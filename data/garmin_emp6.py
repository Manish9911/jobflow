import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "careers-garmin.icims.com" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

R = "5397892_PersonProfileFields."

def sel_info(sid):
    return f.evaluate("""(id) => {
      const e = document.getElementById(id);
      if (!e) return null;
      return {tag: e.tagName, opts: e.tagName === 'SELECT' ? [...e.options].map(o => o.text).slice(0, 15) : null, val: e.value};
    }""", sid)

print("start month:", sel_info(R + "rcf3214_Month"))
print("end month:", sel_info(R + "rcf3215_Month"))
print("start year:", sel_info(R + "rcf3214_Year"))
print("emp:", f.evaluate("""(n) => { const e = document.querySelector("input[name='\" + n + \"']"); return e ? e.value : null; }""", R + "rcf3212"))
print("title:", f.evaluate("""(n) => { const e = document.querySelector("input[name='\" + n + \"']"); return e ? e.value : null; }""", R + "rcf3213"))
b.close()
