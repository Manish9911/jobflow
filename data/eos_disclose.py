import sys, time, json
import playwright.sync_api as pw

b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "autofillWithResume" in p.url)

def list_open_options():
    return page.evaluate(
        """() => {
          const seen = {};
          const out = [];
          const els = document.querySelectorAll("li, div, span");
          for (const e of els) {
            const r = e.getBoundingClientRect();
            if (r.width < 100 || r.height < 12) continue;
            const t = (e.innerText || "").trim();
            if (t.length < 2 || t.length > 90) continue;
            if (t.indexOf(String.fromCharCode(10)) !== -1) continue;
            if (t.startsWith("Please") || t.startsWith("Are ") || t.startsWith("Will ") || t.startsWith("What ") || t.startsWith("Have ") || t.startsWith("You ") || t === "Select One" || t === "Save and Continue" || t === "Back") continue;
            if (!seen[t]) { seen[t] = 1; out.push(t); }
          }
          return out;
        }"""
    )

def click_option(answer):
    res = page.evaluate(
        """(t) => {
          const cands = [...document.querySelectorAll("li, div, span")].filter(e => {
            const r = e.getBoundingClientRect();
            const x = (e.innerText||"").trim();
            return r.width > 0 && r.height > 0 && x.length > 1 && (x === t || x.indexOf(t) !== -1);
          });
          if (!cands.length) return {err: "no-option"};
          cands.sort((a, bb) => (a.getBoundingClientRect().width*a.getBoundingClientRect().height) - (bb.getBoundingClientRect().width*bb.getBoundingClientRect().height));
          const e = cands[0];
          e.scrollIntoView({block: "center"});
          const r = e.getBoundingClientRect();
          return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), txt: (e.innerText||"").trim().slice(0,60)};
        }""",
        answer,
    )
    if res.get("err"):
        return False
    page.mouse.click(res["x"], res["y"])
    time.sleep(1.5)
    return True

TASKS = [
    ("personalInfoUS--ethnicity", "Asian"),
    ("personalInfoUS--gender", "Male"),
    ("personalInfoUS--hispanicOrLatino", "No"),
    ("personalInfoUS--veteranStatus", "protected veteran"),
]

for btn_id, answer in TASKS:
    page.evaluate("() => document.body.click()")
    time.sleep(0.4)
    page.locator("#" + btn_id).click(timeout=8000)
    time.sleep(2)
    opts = list_open_options()
    print("== " + btn_id + " options:", json.dumps(opts))
    ok = click_option(answer)
    print("   picked:", answer, "ok" if ok else "FAIL")
    time.sleep(0.5)

# terms
page.evaluate(
    """() => {
      const c = document.getElementById("termsAndConditions--acceptTermsAndAgreements");
      if (c) c.click();
    }"""
)
time.sleep(0.5)
chk = page.evaluate("() => document.getElementById('termsAndConditions--acceptTermsAndAgreements').checked")
print("terms checked:", chk)
b.close()
