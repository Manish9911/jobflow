"""Pick the next drill candidates (best match, unhandled, cap-aware)."""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobflow.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

applied_cos = [r[0] for r in con.execute("""
  SELECT DISTINCT j.company FROM jobs j JOIN applications a ON a.job_id = j.id
  WHERE a.status = 'submitted'
""")]
print("companies with submissions:", sorted(applied_cos))

rows = con.execute("""
  SELECT j.id, j.title, j.company, j.match_score, j.source, j.apply_url
  FROM jobs j
  WHERE j.passes_filters = 1 AND j.apply_url IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM applications a WHERE a.job_id = j.id
                    AND a.status NOT IN ('failed','rejected_jd','rejected_fraud','flagged_fraud_review'))
    AND (j.match_score IS NULL OR j.match_score >= 50)
  ORDER BY (j.match_score IS NULL), j.match_score DESC, j.id DESC
  LIMIT 30
""").fetchall()
print(f"\nnext candidates: {len(rows)}")
for r in rows:
    skip = r["company"] in applied_cos
    print(f'{"SKIP " if skip else ""}id={r["id"]:>5} score={r["match_score"]} src={r["source"]} | {r["title"][:55]} @ {r["company"][:25]}')
