import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

# Inspect how the country select is wired
out = f.evaluate(r"""() => {
  const sel = document.querySelector("select[name='5397892_PersonProfileFields.rcf3218']");
  const info = {
    html: sel ? sel.outerHTML.slice(0, 400) : null,
    id: sel ? sel.id : null,
  };
  // look for data-attrs
  if (sel) for (const a of sel.attributes) info[a.name] = a.value;
  return info;
}""")
print(json.dumps(out, indent=1))

# Try: select blank, change event, wait, check options
out2 = f.evaluate(r"""() => {
  const sel = document.querySelector("select[name='5397892_PersonProfileFields.rcf3218']");
  sel.value = "";
  sel.dispatchEvent(new Event("change", {bubbles: true}));
  return sel.options.length;
}""")
time.sleep(3)
out3 = f.evaluate(r"""() => [...document.querySelector("select[name='5397892_PersonProfileFields.rcf3218']").options].slice(0, 20).map(o => o.text)""")
print("after change:", out2, "->", out3)
b.close()
