import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

def set_textarea(name, val):
    return page.evaluate("""(a) => {
      const e = document.querySelector("textarea[name='" + a[0] + "']");
      if (!e) return 'no el';
      e.focus();
      const s = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [name, val])

# identify textareas by their label order
tas = page.evaluate(r"""() => {
  const res = [];
  document.querySelectorAll('textarea').forEach(e => {
    let lab = '';
    if (e.id) {
      const l = document.querySelector('label[for="' + e.id + '"]');
      if (l) lab = l.innerText.replace(/\n+/g, ' ').trim().slice(0, 80);
    }
    if (!lab) {
      const wrap = e.closest('td, div');
      if (wrap) { const l2 = wrap.querySelector('label'); if (l2) lab = l2.innerText.replace(/\n+/g, ' ').trim().slice(0, 80); }
    }
    res.push({name: e.name, id: e.id, lab});
  });
  return res;
}""")
print(json.dumps(tas, indent=1))
b.close()
