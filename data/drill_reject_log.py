"""Log drill-gate rejections (clearance/title) as application rows for user review."""
import sqlite3, datetime, json

con = sqlite3.connect("data/jobflow.db")
con.row_factory = sqlite3.Row
master = con.execute("SELECT id FROM resumes WHERE is_master=1").fetchone()["id"]
now = datetime.datetime.now().isoformat()
rejects = [
    (1147, "rejected_jd", "Clearance (JD): DoD Secret security clearance required - 'Department of Defense Secret security clearance is obtainable within a reasonable time'"),
    (1127, "rejected_jd", "Clearance (JD): 'Secret Clearance Minimum - Can support TS'"),
    (1117, "rejected_jd", "Clearance (JD): 'Active TS/SCI clearance with ability to obtain polygraph'"),
    (388,  "rejected_jd", "Title gate: 'Principal Software Engineer' exceeds seniority cap (Principal/Staff/Director rejected per title rule)"),
]
for jid, status, note in rejects:
    job = con.execute("SELECT id, title, company FROM jobs WHERE id=?", (jid,)).fetchone()
    exists = con.execute("SELECT id FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1", (jid,)).fetchone()
    if exists:
        con.execute("UPDATE applications SET status=?, error_text=?, finished_at=? WHERE id=?", (status, note, now, exists["id"]))
        print(f"job {jid} ({job['company'][:25]}): updated app {exists['id']} -> {status}")
    else:
        cr = con.execute(
            "INSERT INTO applications (job_id, resume_id, dry_run, status, error_text, notes_json, created_at, finished_at) VALUES (?, ?, 0, ?, ?, ?, ?, ?)",
            (jid, master, status, note, json.dumps({"reason": "drill_gates_2026_11_23"}), now, now),
        )
        print(f"job {jid} ({job['company'][:25]}): new app {cr.lastrowid} -> {status}")
con.commit()
con.close()
