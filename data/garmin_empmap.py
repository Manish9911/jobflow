import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate("""() => {
  const names = ["rcf3212","rcf3216","rcf3218","rcf3217","rcf3213","rcf3214_Month","rcf3214_Year","rcf3215_Month","rcf3215_Year","rcf3268"];
  return names.map(n => {
    const els = [...document.querySelectorAll("input, select, textarea")].filter(e => e.name.endsWith("_" + n) || e.name.endsWith("_" + n) && e.name.indexOf("_Month") === -1 || e.name === "5397892_PersonProfileFields." + n);
    const e = els.find(x => x.name.endsWith("." + n)) || els[0];
    if (!e) return {n, found: false};
    let label = "";
    let p = e.closest("tr") || e.parentElement;
    for (let i = 0; i < 8 && p; i++) {
      const l = p.querySelector("label");
      if (l && (l.innerText || "").trim()) { label = l.innerText.trim().slice(0, 70); break; }
      p = p.parentElement;
    }
    const opts = e.tagName === "SELECT" ? [...e.options].slice(0, 10).map(o => o.value + ":" + o.text.slice(0, 25)) : null;
    return {n, label, val: (e.value || "").slice(0, 40), opts};
  });
}""")
print(json.dumps(out, indent=1))
b.close()
