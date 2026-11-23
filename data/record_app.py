import sqlite3, datetime, os, json, sys

DB = os.path.join(os.path.dirname(__file__), "jobflow.db")
JOB_ID = int(sys.argv[1])
RESUME_DIR = sys.argv[2]
COMPANY = sys.argv[3]
ROLE = sys.argv[4]
STATUS = sys.argv[5]
NOTE = sys.argv[6]

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
now = datetime.datetime.now().isoformat()
row = con.execute(
    "SELECT id FROM applications WHERE job_id = ? ORDER BY id DESC LIMIT 1", (JOB_ID,)
).fetchone()
if not row:
    pdfs = [f for f in os.listdir(RESUME_DIR) if f.lower().endswith(".pdf")] if os.path.isdir(RESUME_DIR) else []
    pdf = os.path.join(RESUME_DIR, pdfs[0]) if pdfs else ""
    cr = con.execute(
        "INSERT INTO resumes (profile_id, label, original_filename, storage_path, content_json, is_master, created_at) "
        "VALUES (1, ?, ?, ?, ?, 0, ?)",
        (f"{COMPANY} {ROLE}", os.path.basename(pdf) if pdf else "generated",
         pdf, json.dumps({"builder": "data/build_resume.py", "tailored_for": f"{COMPANY} - {ROLE}"}), now),
    )
    resume_id = cr.lastrowid
    con.execute(
        "INSERT INTO applications (job_id, resume_id, dry_run, status, error_text, notes_json, created_at, finished_at) "
        "VALUES (?, ?, 0, ?, ?, ?, ?, ?)",
        (JOB_ID, resume_id, STATUS, NOTE, json.dumps({"block": "captcha"}), now, now),
    )
    print("created resume", resume_id, "app", con.execute("SELECT last_insert_rowid()").fetchone()[0])
else:
    con.execute(
        "UPDATE applications SET status=?, error_text=?, finished_at=? WHERE id=?",
        (STATUS, NOTE, now, row["id"]),
    )
    print("updated app", row["id"])
con.commit()
con.close()
