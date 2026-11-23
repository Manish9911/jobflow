import sqlite3, datetime, os, json

DB = os.path.join(os.path.dirname(__file__), "jobflow.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
row = con.execute(
    "SELECT id, job_id, status FROM applications WHERE job_id = 8330 ORDER BY id DESC LIMIT 1"
).fetchone()
now = datetime.datetime.now().isoformat()
note = (
    "Dayforce form 100% complete (candidate info + auto-imported work/edu + 5 questionnaire "
    "pages + acknowledgement checked). Submit enabled but invisible reCAPTCHA token not issuing "
    "under CDP automation. USER TO CLICK Submit ONCE in visible Chrome (Java Developer - Digitech, Sarnova Req #382)."
)
if row:
    con.execute("UPDATE applications SET status=?, error_text=?, notes_json=?, finished_at=? WHERE id=?",
                ("submit_blocked_rcaptcha", note, json.dumps({"block": "invisible_recaptcha", "needs": "user_click_submit"}), now, row["id"]))
    print("updated app", row["id"])
else:
    # create tailored resume row for Digitech first
    digi_dir = os.path.join(os.path.dirname(__file__), "exports", "digitech")
    pdfs = [f for f in os.listdir(digi_dir) if f.lower().endswith(".pdf")] if os.path.isdir(digi_dir) else []
    pdf = os.path.join(digi_dir, pdfs[0]) if pdfs else ""
    cur = con.execute(
        "INSERT INTO resumes (profile_id, label, original_filename, storage_path, content_json, is_master, created_at) "
        "VALUES (1, ?, ?, ?, ?, 0, ?)",
        ("Digitech Java Developer",
         os.path.basename(pdf) if pdf else "generated (deterministic)",
         pdf,
         json.dumps({"builder": "data/build_resume.py", "content": "data/exports/digitech_content.json", "tailored_for": "Digitech - Java Developer (Sarnova)"}),
         now),
    )
    resume_id = cur.lastrowid
    cur = con.execute(
        "INSERT INTO applications (job_id, resume_id, dry_run, status, error_text, notes_json, created_at, finished_at) "
        "VALUES (8330, ?, 0, ?, ?, ?, ?, ?)",
        (resume_id, "submit_blocked_rcaptcha", note, json.dumps({"block": "invisible_recaptcha", "needs": "user_click_submit"}), now, now),
    )
    print("created resume", resume_id, "app", cur.lastrowid)
con.commit()
con.close()
