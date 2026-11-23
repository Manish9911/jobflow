import json, time
import playwright.sync_api as pw
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
page = next(p for p in ctx.pages if "mode=apply" in p.url)
f = next(ff for ff in page.frames if "in_iframe=1" in ff.url)
out = f.evaluate(r"""() => {
  const sel = document.querySelector("select[name='5397892_PersonProfileFields.rcf3218']");
  let p = sel.parentElement;
  const chain = [];
  for (let i = 0; i < 5 && p; i++) {
    chain.push({
      tag: p.tagName,
      cls: (p.className || "").toString().slice(0, 120),
      id: p.id,
      html: p.outerHTML.slice(0, 300)
    });
    p = p.parentElement;
  }
  return chain;
}""")
for c in out:
    print(c['tag'], c['id'], c['cls'])
    print('   ', c['html'][:280].replace('\n', ' '))
    print()
b.close()
