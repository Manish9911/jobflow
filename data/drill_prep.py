"""Drill prep: gate-check each candidate (JD + title + fraud), build a
WHY/WHAT/PROOF tailored resume for each that passes. No browser work here."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.db.base import make_engine, make_session  # noqa: E402
from backend.app.db.models import Job  # noqa: E402
from backend.app.services.eligibility import assess_jd, assess_title  # noqa: E402
from backend.app.services.fraud import assess_job_fraud  # noqa: E402
from backend.app.services.tailor import fetch_jd  # noqa: E402

IDS = [int(a) for a in sys.argv[1:]] or [1147, 1148, 1127, 1117, 1067]
HERE = os.path.dirname(os.path.abspath(__file__))

engine = make_engine("sqlite:///C:/Users/badug/jobflow/data/jobflow.db")
db = make_session(engine)()
for jid in IDS:
    job = db.get(Job, jid)
    if not job:
        print(f"[{jid}] NOT FOUND")
        continue
    title = job.title or ""
    company = job.company or ""
    jd = fetch_jd(job) or ""
    jd = (jd or "").strip()

    ta = assess_title(title)
    ja = assess_jd(jd) if jd else {"decision": "apply", "reasons": [], "checked": False}
    fr = assess_job_fraud(jd, job.apply_url, getattr(job, "company_website", None))

    verdict = "APPLY"
    why = []
    if ta["decision"] == "reject":
        verdict, why = "REJECT(title)", ta["reasons"]
    if ja["decision"] == "reject":
        verdict, why = "REJECT(jd)", ja["reasons"]
    if fr["decision"] == "reject":
        verdict, why = "REJECT(fraud)", fr["reasons"]
    if fr["decision"] == "review":
        if verdict == "APPLY":
            verdict, why = "REVIEW(fraud)", fr["reasons"]

    print(f"\n=== [{jid}] {title} @ {company}")
    print(f"    jd_chars={len(jd)} verdict={verdict}")
    if why:
        for w in why:
            print(f"      - {w[:160]}")

    if verdict == "APPLY":
        # keywords: JD skills (deterministic tailoring)
        from backend.app.ingestion.match import SKILL_VOCAB
        import re as _re
        jdt = _re.sub(r"\s+", " ", jd)
        kws = [lab for lab, rx in SKILL_VOCAB.items() if rx.search(jdt)]
        kw = ",".join(kws)
        out = os.path.join(HERE, "exports", f"drill_{jid}.json")
        subprocess.run(
            [sys.executable, os.path.join(HERE, "build_content.py"),
             "--keywords", kw, "--title", "Software Development Engineer", "--out", out],
            check=True, capture_output=True, text=True)
        print(f"    content -> {out} (jd skills: {kws})")
db.close()
print("\nprep done")
