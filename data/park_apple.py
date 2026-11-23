"""Park Apple (1060): apply flow requires an Apple ID (phone/SMS verification)."""
import sqlite3, datetime, json

con = sqlite3.connect("data/jobflow.db")
con.row_factory = sqlite3.Row
master = con.execute("SELECT id FROM resumes WHERE is_master=1").fetchone()["id"]
now = datetime.datetime.now().isoformat()
jid = 1060
row = con.execute("SELECT id FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1", (jid,)).fetchone()
note = ("Apple careers requires an Apple ID sign-in to apply ('Submit Resume' -> idmsa.apple.com). "
        "No guest path. New Apple ID needs phone/SMS verification (human step). "
        "Resume ready: data/exports/apple_resume.docx (2 pages, WWP).")
if row:
    con.execute("UPDATE applications SET status='needs_manual', error_text=?, finished_at=? WHERE id=?",
                (note, now, row["id"]))
    print(f"app {row['id']} parked")
else:
    cr = con.execute(
        "INSERT INTO applications (job_id, resume_id, dry_run, status, error_text, notes_json, created_at, finished_at) "
        "VALUES (?, ?, 0, 'needs_manual', ?, ?, ?, ?)",
        (jid, master, note, json.dumps({"block": "apple_id_required", "resume": "data/exports/apple_resume.docx"}), now, now))
    print(f"new app {cr.lastrowid} parked")
con.commit()
con.close()
