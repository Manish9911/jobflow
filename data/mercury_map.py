import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "candidate?from=login" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
time.sleep(3)
out = f.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('input, select, textarea').forEach(e => {
    if (e.type === 'hidden') return;
    const wrap = e.closest('tr') || e.closest('div');
    const ctx2 = wrap ? wrap.innerText.replace(/\n+/g, ' | ').trim().slice(0, 120) : '';
    let opts = null;
    if (e.tagName === 'SELECT') opts = [...e.options].map(o => o.value + '=' + o.text.trim()).slice(0, 20);
    res.push({name: e.name, id: e.id, type: e.type, tag: e.tagName, val: (e.value || '').slice(0, 40), req: !!(e.hasAttribute('required') || (e.getAttribute('i_required')==='true')), ctx: ctx2, opts});
  });
  return res;
}""")
with open("C:/Users/badug/jobflow/data/evidence/mercury_fields.json", "w") as fh:
    json.dump(out, fh, indent=1)
for o in out:
    line = f"{o['name']} | {o['type']}/{o['tag']} | val={o['val']!r} req={o['req']}"
    if o.get("opts"): line += " OPTS=" + str(o["opts"])[:200]
    if o.get("ctx"): line += " | " + o["ctx"][:90]
    print(line)
b.close()
