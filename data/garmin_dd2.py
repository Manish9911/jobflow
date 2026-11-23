import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll("[id*='rcf3218']").forEach(e => {
    const r = e.getBoundingClientRect();
    res.push({tag: e.tagName, id: e.id, cls: (e.className||'').toString().slice(0,80), vis: r.width > 0 && r.height > 0, w: Math.round(r.width), h: Math.round(r.height)});
  });
  // also find visible element showing 'India' near the country label
  const label = document.querySelector("label[for='5397892_PersonProfileFields.rcf3218']");
  if (label) {
    let cell = label.closest(".iCIMS_TableCell") || label.parentElement;
    if (cell) {
      res.push({tag: 'CELL', html: cell.innerHTML.slice(0, 600)});
    }
  }
  return res;
}""")
for o in out:
    print(o)
    print()
b.close()
