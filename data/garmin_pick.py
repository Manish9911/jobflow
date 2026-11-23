import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)

name = "5397892_PersonProfileFields.rcf3218"

# computed style of the select
st = f.evaluate("""(n) => {
  const s = document.getElementById(n);
  const cs = getComputedStyle(s);
  return {display: cs.display, visibility: cs.visibility, opacity: cs.opacity, pos: cs.position};
}""", name)
print("select style:", st)

# click the visible anchor
f.evaluate("""(n) => {
  const a = document.getElementById(n + '_icimsDropdown');
  a.scrollIntoView({block: 'center'});
  a.click();
  return 'clicked';
}""", name)
time.sleep(1)
# who is focused now?
print("focused:", f.evaluate("() => document.activeElement ? document.activeElement.tagName + '#' + document.activeElement.id : 'none'"))
st2 = f.evaluate("""(n) => {
  const s = document.getElementById(n);
  const cs = getComputedStyle(s);
  const cont = document.getElementById(n + '_icimsDropdown_ctnr');
  return {display: cs.display, ctnr: cont.className, focused: document.activeElement === s};
}""", name)
print("after click:", st2)
b.close()
