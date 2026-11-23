import sys, json, urllib.request, html as H, re

targets = [
    (1375, "chime",   "8765684002"),
    (2478, "cloudflare","8038898"),
    (4490, "databricks","8233899002"),
    (5857, "figma",   "5551532004"),
    (6171, "vercel",  "6137958004"),
    (3643, "elastic", "8352180"),
    (3652, "elastic", "8378070"),
    (3654, "elastic", "8318197"),
    (3204, "gitlab",  "8911684002"),
    (3205, "gitlab",  "8891836002"),
]
out = []
for jid, board, gid in targets:
    url = "https://boards.api.greenhouse.io/v1/boards/%s/jobs/%s" % (board, gid)
    txt, err = "", ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        content = data.get("content", "") or ""
        if isinstance(content, dict):
            content = json.dumps(content)
        txt = re.sub(r"<[^>]+>", " ", content)
        txt = H.unescape(txt)
        txt = re.sub(r"\s+", " ", txt)
    except Exception as e:
        err = str(e)
    out.append({"jid": jid, "board": board, "gid": gid, "err": err, "text": txt})

with open(r"C:\Users\badug\jobflow\data\prescreen_out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False)
for d in out:
    if d["err"]:
        print("%s (%d) ERROR: %s" % (d["board"], d["jid"], d["err"]))
        continue
    t = d["text"].lower()
    flags = []
    for kw in ["clearance", "classified", "u.s. person", "visa", "sponsorship", "sponsor",
               "stem opt", "work authorization", "authorized to work", "eligible to work",
               "years of experience", "year of experience"]:
        for m in re.finditer(re.escape(kw), t):
            i = m.start()
            flags.append(kw.upper() + " :: ...%s..." % t[max(0, i-80):i+100])
            break
    print("\n==== %s (jid %d) len=%d" % (d["board"], d["jid"], len(d["text"])))
    for fl in flags[:8]:
        print("   ", fl)
    if not flags:
        print("    (no auth/experience keywords)")
