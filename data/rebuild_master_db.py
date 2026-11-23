"""Rebuild the DB master resume row from the upgraded (WHY/WHAT/PROOF) docx."""
import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_resume import parse_master  # noqa: E402

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobflow.db")

m = parse_master()
n_wwp = 0
for j in m["jobs"]:
    n_wwp += sum(1 for b in j["bullets"] if b.startswith("To "))
    print(f'{j["company"].split(",")[0].strip()}: {len(j["bullets"])} bullets')
print(f"WHY-led bullets parsed from upgraded docx: {n_wwp}/38")

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute(
    "SELECT id, is_master, label, original_filename, storage_path FROM resumes WHERE is_master=1"
).fetchall()
print("master rows:", [(r["id"], r["label"], r["storage_path"]) for r in rows])
if not rows:
    print("no master row — nothing to update")
    sys.exit(0)

content = json.dumps(m, ensure_ascii=False)
for r in rows:
    con.execute(
        "UPDATE resumes SET content_json = ? WHERE id = ?",
        (content, r["id"]),
    )
    print(f"updated resume id {r['id']} content_json ({len(content)} chars)")
con.commit()
con.close()
print("done")
