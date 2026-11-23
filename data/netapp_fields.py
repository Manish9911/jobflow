import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)
out = page.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('input, select, textarea').forEach(e => {
    if (e.type === 'hidden' || e.type === 'button') return;
    let lab = '';
    const id = e.id;
    if (id) {
      const l = document.querySelector('label[for="' + id + '"]');
      if (l) lab = l.innerText.replace(/\n+/g, ' ').trim().slice(0, 90);
    }
    if (!lab) {
      const wrap = e.closest('td, .profileData, div');
      if (wrap) {
        const l2 = wrap.querySelector('label');
        if (l2) lab = l2.innerText.replace(/\n+/g, ' ').trim().slice(0, 90);
      }
    }
    res.push({name: e.name, id: id, type: e.type, tag: e.tagName, lab, val: (e.value || '').slice(0, 25)});
  });
  return res;
}""")
with open("C:/Users/badug/jobflow/data/evidence/netapp_fields.json", "w") as fh:
    json.dump(out, fh, indent=1)
for o in out:
    print(f"{o['name']} | {o['type']}/{o['tag']} | val={o['val']!r} | {o['lab'][:80]}")
b.close()
