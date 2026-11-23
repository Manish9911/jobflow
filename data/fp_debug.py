"""Show the exact fraud/YOE match contexts for the false-positive jobs."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.app.db.base import make_engine, make_session  # noqa: E402
from backend.app.db.models import Job  # noqa: E402
from backend.app.services.tailor import fetch_jd  # noqa: E402
from backend.app.services.fraud import _FEE_PATTERNS, _ID_DOC_PATTERNS  # noqa: E402
from backend.app.services.eligibility import required_experience_years  # noqa: E402

engine = make_engine("sqlite:///C:/Users/badug/jobflow/data/jobflow.db")
db = make_session(engine)()

for jid in (1148, 1067, 1147, 1117):
    job = db.get(Job, jid)
    jd = (fetch_jd(job) or "").strip()
    print(f"\n=== [{jid}] {job.title[:60]} — jd_chars={len(jd)}")
    text = re.sub(r"\s+", " ", jd)
    for pat, name in ((_FEE_PATTERNS, "FEE"), (_ID_DOC_PATTERNS, "IDDOC")):
        for m in pat.finditer(text):
            s, e = max(0, m.start() - 60), min(len(text), m.end() + 60)
            print(f"  {name} MATCH: ...{text[s:e]}...")
    y = required_experience_years(text)
    if y:
        idx = text.lower().find(str(y))
        print(f"  YOE MATCH: {y} -> ...{text[max(0, idx - 60):idx + 80]}...")
db.close()
