"""Park BofA (1067): Workday account-creation step is human-gated (isUserHuman() wall)."""
import sqlite3, datetime, json

con = sqlite3.connect("data/jobflow.db")
con.row_factory = sqlite3.Row
master = con.execute("SELECT id FROM resumes WHERE is_master=1").fetchone()["id"]
now = datetime.datetime.now().isoformat()
jid = 1067
row = con.execute("SELECT id FROM applications WHERE job_id=? ORDER BY id DESC LIMIT 1", (jid,)).fetchone()
note = ("Workday human-interaction wall at step 1/8 (Create Account): createAccountSubmit is gated by "
        "isUserHuman() which fails for automated sessions. Form was filled (email + generated password "
        "saved in data/portal_credentials.json, BofA/Workday entry). Resume ready: data/exports/bofa_resume.docx. "
        "User click on 'Create Account' unblocks steps 2-8.")
if row:
    con.execute("UPDATE applications SET status='submit_blocked_captcha', error_text=?, finished_at=? WHERE id=?",
                (note, now, row["id"]))
    print(f"app {row['id']} parked")
else:
    cr = con.execute(
        "INSERT INTO applications (job_id, resume_id, dry_run, status, error_text, notes_json, created_at, finished_at) "
        "VALUES (?, ?, 0, 'submit_blocked_captcha', ?, ?, ?, ?)",
        (jid, master, note, json.dumps({"block": "workday_isUserHuman_wall", "resume": "data/exports/bofa_resume.docx"}), now, now))
    print(f"new app {cr.lastrowid} parked")
con.commit()
con.close()
