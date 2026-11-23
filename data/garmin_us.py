import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

def pick_country(name, text):
    sel = f.locator(f"select[name='{name}']")
    sel.scroll_into_view_if_needed()
    sel.click()
    time.sleep(0.8)
    sel.press("Control+a")
    time.sleep(0.2)
    for ch in text:
        sel.press(ch.lower())
        time.sleep(0.06)
    time.sleep(2.5)
    opts = f.evaluate(r"""(n) => {
      const lb = document.querySelector("[id='" + n.replace(/'/g, "") + "_listbox']") || document.querySelector("[id*='_listbox']");
      if (!lb) return null;
      return [...lb.querySelectorAll("li, [role=option]")].map(o => o.textContent.trim()).slice(0, 15);
    }""", name)
    print("opts for", name.split(".")[-1], ":", opts)
    if opts:
        clicked = f.evaluate(r"""(args) => {
          const lb = document.querySelector("[id='" + args[0].replace(/'/g, "") + "_listbox']") || document.querySelector("[id*='_listbox']");
          const it = [...lb.querySelectorAll("li, [role=option]")].find(o => o.textContent.trim().toLowerCase().startsWith(args[1].toLowerCase()));
          if (!it) return "no item";
          it.click();
          return "clicked: " + it.textContent.trim();
        }""", [name, text])
        print(clicked)
        time.sleep(1.5)
    val = f.evaluate("""(n) => document.querySelector("select[name='" + n + "']").value""", name)
    print("value now:", val)

pick_country("5397892_PersonProfileFields.rcf3218", "United States")
b.close()
