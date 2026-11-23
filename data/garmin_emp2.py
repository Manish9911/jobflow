import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def click_add_more():
    return f.evaluate("""() => {
      const els = [...document.querySelectorAll("a, button, input")];
      const b = els.find(x => /add more \(professional experience\)/i.test((x.innerText || x.value || "").trim()));
      if (!b) return "not found";
      b.click();
      return "clicked";
    }""")

print(click_add_more())
time.sleep(2)
print(click_add_more())
time.sleep(2)

# now list all rcf3212 (employer) fields with their full names to identify group prefixes
out = f.evaluate("""() => [...document.querySelectorAll("input[name*='rcf3212']")].map(e => ({name: e.name, val: e.value}))""")
print(json.dumps(out, indent=1))
b.close()
