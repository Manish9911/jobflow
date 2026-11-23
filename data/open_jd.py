import sys, time, json
import urllib.request
import urllib.parse
import playwright.sync_api as pw

url = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else None
req = urllib.request.Request('http://127.0.0.1:9334/json/new?' + urllib.parse.quote(url, safe=''), method='PUT')
t = json.loads(urllib.request.urlopen(req, timeout=15).read())
tid = t['id']
time.sleep(10)
b = pw.sync_playwright().start().chromium.connect_over_cdp("http://127.0.0.1:9334")
ctx = b.contexts[0]
host = urllib.parse.urlparse(url).netloc
page = next((p for p in ctx.pages if host in p.url), None)
if page is None:
    raise SystemExit("tab not found among: " + ", ".join(p.url for p in ctx.pages))
time.sleep(3)
txt = page.evaluate("() => document.body.innerText")
low = txt.lower()
keys = {k: (k in low) for k in ["clearance", "sponsor", "stem opt", "h1b", "itar", "citizen", "us person", "years of experience", "work authorization"]}
print("GATES:", json.dumps(keys))
open(out, "w", encoding="utf-8") if out else None
if out:
    open(out, "w", encoding="utf-8").write(txt)
print("LEN:", len(txt))
print("TITLE:", page.title())
print(txt[:600])
urllib.request.urlopen('http://127.0.0.1:9334/json/close/' + tid, timeout=10)
b.close()
