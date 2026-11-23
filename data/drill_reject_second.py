"""Batch-log the second-app drill rejections (2026-11-23)."""
import datetime
import json
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobflow.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
master = con.execute("SELECT id FROM resumes WHERE is_master=1").fetchone()["id"]
now = datetime.datetime.now().isoformat()

# (job_id, reason)
REJECTS = [
    (7845, "title: Staff level"),
    (7844, "title: Staff level"),
    (7843, "title: Staff level"),
    (7756, "field mismatch: ML/LLM engineering (no ML experience; truth contract)"),
    (7755, "field mismatch: ML/LLM engineering (no ML experience; truth contract)"),
    (7754, "field mismatch: ML/LLM engineering (no ML experience; truth contract)"),
    (7753, "field mismatch: ML/LLM engineering (no ML experience; truth contract)"),
    (7696, "field mismatch: agentic LLM systems (no ML experience; truth contract)"),
    (7695, "field mismatch: agentic LLM systems (no ML experience; truth contract)"),
    (1949, "title: Staff level"),
    (1913, "title: Principal level"),
    (4778, "not SWE: Partner Marketing Manager"),
    (4649, "field mismatch: Solutions Architect AI/ML (healthcare), specialist/architect level"),
    (3351, "title: Staff Product Manager"),
    (7878, "field mismatch: threat intelligence platforms (Python/Go, security-ops domain)"),
    (7868, "title: Staff level"),
    (7867, "title: Staff level"),
    (7866, "title: Staff level"),
    (7865, "title: Staff level"),
    (7864, "title: Staff level"),
    (7863, "title: Staff level"),
    (7862, "title: Staff level"),
    (7861, "title: Staff level"),
    (7860, "title: Staff level"),
    (7859, "title: Staff level"),
    (7858, "title: Staff level"),
    (7857, "title: Staff level"),
    (7855, "title: Staff level"),
    (7854, "title: Staff level"),
    (7853, "title: Staff level"),
    (7852, "title: Staff level"),
    (7851, "title: Staff level"),
    (7850, "title: Staff level"),
    (7849, "title: Staff level"),
    (7848, "title: Staff level"),
    (7847, "title: Staff level"),
    (7846, "title: Staff level"),
    (7841, "title: Staff Data Engineer"),
    (7839, "title: Staff Analytics Engineer"),
]

for jid, reason in REJECTS:
    row = con.execute(
        "SELECT id, status FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1", (jid,)).fetchone()
    if row and row["status"] in ("submitted",):
        print(f"SKIP {jid}: already {row['status']}")
        continue
    notes = json.dumps({"drill": "2026-11-23-second-app", "reason": reason})
    if row:
        con.execute(
            "UPDATE applications SET status='rejected_jd', error_text=?, notes_json=?, finished_at=? WHERE id=?",
            (reason, notes, now, row["id"]))
        print(f"updated app {row['id']} <- {jid}")
    else:
        cr = con.execute(
            "INSERT INTO applications (job_id, resume_id, dry_run, status, error_text, notes_json, created_at, finished_at) "
            "VALUES (?, ?, 0, 'rejected_jd', ?, ?, ?, ?)",
            (jid, master, reason, notes, now, now))
        print(f"new app {cr.lastrowid} <- {jid}")

con.commit()
con.close()
print(f"done: {len(REJECTS)} rejections")
