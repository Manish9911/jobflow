import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "successfactors" in p.url)
time.sleep(3)

def set_text(name, val):
    return page.evaluate("""(a) => {
      const e = document.querySelector("input[name='" + a[0] + "'], textarea[name='" + a[0] + "']");
      if (!e) return 'no el';
      e.focus();
      const proto = e.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
      const s = Object.getOwnPropertyDescriptor(proto, 'value').set;
      s.call(e, a[1]);
      e.dispatchEvent(new Event('input', {bubbles: true}));
      e.dispatchEvent(new Event('change', {bubbles: true}));
      e.blur();
      return 'ok';
    }""", [name, val])

print('phone:', set_text('cellPhone', '+1 940-843-6058'))
print('address:', set_text('address', 'Almond Willow CV'))
print('city:', set_text('city', 'Collierville'))
print('zip:', set_text('zip', '38017'))
print('employer:', set_text('custRecentEmployementCoName', 'Verizon Communications'))
print('title:', set_text('custRecentEmployementendTitle', 'Sr. Java Full Stack Developer'))
print('inst:', set_text('custRecentEducationInsititeName', 'Christian Brothers University'))
print('instcity:', set_text('custRecentEducationInstituteCity', 'Memphis'))
# state field: unnamed — find input whose nearest label is 'Current State'
r = page.evaluate(r"""() => {
  const inp = document.querySelector("input[aria-label='Current State'], input[id*='state']");
  if (!inp) {
    // fallback: find by label text
    const labels = [...document.querySelectorAll('label')].filter(l => /current state/i.test(l.innerText || ''));
    if (!labels.length) return 'no label';
    const forid = labels[0].getAttribute('for');
    const e2 = forid ? document.getElementById(forid) : null;
    if (!e2) return 'no for-id';
    const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    s.call(e2, 'Tennessee');
    e2.dispatchEvent(new Event('input', {bubbles: true}));
    e2.dispatchEvent(new Event('change', {bubbles: true}));
    return 'ok via for-id';
  }
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  s.call(inp, 'Tennessee');
  inp.dispatchEvent(new Event('input', {bubbles: true}));
  inp.dispatchEvent(new Event('change', {bubbles: true}));
  return 'ok';
}""")
print('state:', r)
print('inststate:', page.evaluate(r"""() => {
  const labels = [...document.querySelectorAll('label')].filter(l => /institution state/i.test(l.innerText || ''));
  if (!labels.length) return 'no label';
  const forid = labels[0].getAttribute('for');
  const e2 = forid ? document.getElementById(forid) : null;
  if (!e2) return 'no for-id';
  const s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  s.call(e2, 'Tennessee');
  e2.dispatchEvent(new Event('input', {bubbles: true}));
  e2.dispatchEvent(new Event('change', {bubbles: true}));
  return 'ok';
}"""))
b.close()
