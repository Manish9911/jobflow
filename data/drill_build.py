"""Build WHY/WHAT/PROOF tailored DOCX for one job + print its apply URL."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))

from backend.app.db.base import make_engine, make_session  # noqa: E402
from backend.app.db.models import Job  # noqa: E402
from backend.app.services.tailor import fetch_jd  # noqa: E402
from backend.app.ingestion.match import SKILL_VOCAB  # noqa: E402
import re  # noqa: E402

JID = int(sys.argv[1])
engine = make_engine("sqlite:///C:/Users/badug/jobflow/data/jobflow.db")
db = make_session(engine)()
job = db.get(Job, JID)
print(f"JOB {job.id} | {job.title} @ {job.company}")
print(f"APPLY_URL: {job.apply_url}")
print(f"LOCATION: {job.location}")

jd = re.sub(r"\s+", " ", fetch_jd(job) or "")
kws = [lab for lab, rx in SKILL_VOCAB.items() if rx.search(jd)]
print(f"JD SKILLS: {kws}")

content = os.path.join(HERE, "exports", f"drill_{job.id}.json")
subprocess.run([sys.executable, os.path.join(HERE, "build_content.py"),
                "--keywords", ",".join(kws),
                "--title", "Software Development Engineer",
                "--out", content], check=True, capture_output=True, text=True)
c = json.load(open(content))
n_wwp = sum(1 for j in c["jobs"] for b in j["bullets"] if b.startswith("To "))
ntot = sum(len(j["bullets"]) for j in c["jobs"])
print(f"CONTENT: {content} | bullets {n_wwp}/{ntot} WHY-led")

docx = os.path.join(HERE, "exports", f"Manish_Badugu_{job.company.split()[0]}_{JID}.docx")
subprocess.run([sys.executable, os.path.join(HERE, "build_resume.py"),
                "--content", content, "--company", job.company,
                "--role", "Software Development Engineer",
                "--keywords", ",".join(kws), "--out", docx],
               check=True, capture_output=True, text=True)
print(f"DOCX: {docx} ({os.path.getsize(docx)} bytes)")
db.close()
