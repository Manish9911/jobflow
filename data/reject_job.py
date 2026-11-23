"""Reject a job at pre-screen. Usage:
python data/reject_job.py <job_id> <status> <quote>
e.g. python data/reject_job.py 8302 rejected_clearance "Final Clearance for the Role: Top Secret."
"""
import json
import sqlite3
import sys

job_id = int(sys.argv[1])
status = sys.argv[2]
quote = sys.argv[3] if len(sys.argv) > 3 else ""

con = sqlite3.connect("data/jobflow.db")
cur = con.execute(
    """INSERT INTO applications (job_id, resume_id, status, dry_run, notes_json, created_at, finished_at)
       VALUES (?, 1, ?, 0, ?, datetime('now'), datetime('now'))""",
    (job_id, status, json.dumps({"reason": status.replace("rejected_", ""), "quote": quote})),
)
reason = status.replace("rejected_", "")
con.execute(
    "UPDATE jobs SET jd_eligibility_json = ? WHERE id = ?",
    (json.dumps({"decision": "reject", "reason": reason, "quote": quote}), job_id),
)
con.commit()
print(f"rejected job {job_id} as {status} -> app {cur.lastrowid}")
