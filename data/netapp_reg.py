import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)
# map fields
out = page.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('input, select').forEach(e => {
    if (e.type === 'hidden') return;
    const lab = e.labels && e.labels.length ? e.labels[0].innerText.replace(/\n+/g,' ').trim().slice(0,60) : '';
    res.push({name: e.name, id: e.id, type: e.type, tag: e.tagName, lab});
  });
  return res;
}""")
for o in out:
    print(o)
b.close()
