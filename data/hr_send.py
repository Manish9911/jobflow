import time, json
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "highroller-careers.com" in p.url)

chip = page.evaluate(
    """() => {
      const t = document.body.innerText;
      const i = t.indexOf("CV or resume");
      return t.slice(i, i + 220);
    }"""
)
print("CV area:", repr(chip))
if "Manish Badugu High Roller" not in chip:
    print("CV NOT ATTACHED - re-uploading")
    cv = r"C:/Users/badug/jobflow/data/exports/highroller/Manish Badugu High Roller Senior Software Engineer.pdf"
    page.locator('input[name="candidate.cv"]').set_input_files(cv)
    time.sleep(5)
    chip = page.evaluate("""() => { const t = document.body.innerText; const i = t.indexOf("CV or resume"); return t.slice(i, i + 220); }""")
    print("CV area now:", repr(chip))

btn = page.evaluate(
    """() => {
      const b = [...document.querySelectorAll("button, a")].find(x => (x.innerText||'').trim() === 'Send' && x.getBoundingClientRect().width > 0);
      if (!b) return null;
      b.scrollIntoView({block: 'center'});
      const r = b.getBoundingClientRect();
      return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), disabled: b.disabled};
    }"""
)
print("send btn:", btn)
if btn and not btn.get("disabled"):
    page.mouse.click(btn["x"], btn["y"])
    time.sleep(12)
    print("URL now:", page.url)
    txt = page.evaluate("() => document.body.innerText")
    print(txt[:1200])
b.close()
