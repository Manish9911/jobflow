"""Second-application batch: companies with exactly 1 prior submission (cap=2)."""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jobflow.db")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# companies with exactly one submitted application
one_cos = [r[0] for r in con.execute("""
  SELECT j.company FROM jobs j JOIN applications a ON a.job_id = j.id
  WHERE a.status = 'submitted'
  GROUP BY j.company HAVING COUNT(*) = 1
""")]
print(f"companies with exactly 1 submission: {len(one_cos)}")

rows = con.execute("""
  SELECT j.id, j.title, j.company, j.match_score, j.source,
         (SELECT a.error_text FROM applications a WHERE a.job_id = j.id ORDER BY a.id DESC LIMIT 1) AS last_app
  FROM jobs j
  WHERE j.passes_filters = 1 AND j.apply_url IS NOT NULL
    AND j.company IN ({ph})
    AND NOT EXISTS (SELECT 1 FROM applications a WHERE a.job_id = j.id
                    AND a.status NOT IN ('failed','rejected_jd','rejected_fraud','flagged_fraud_review','submit_failed'))
    AND (j.match_score IS NULL OR j.match_score >= 70)
  ORDER BY (j.match_score IS NULL), j.match_score DESC, j.id DESC
  LIMIT 40
""".format(ph=",".join("?" * len(one_cos))), one_cos).fetchall()
print(f"candidates (score>=70, company has room for 2nd app): {len(rows)}")
for r in rows:
    print(f'id={r["id"]:>5} score={r["match_score"]:>3} src={r["source"][:12]:12} | {r["title"][:50]} @ {r["company"][:28]}')
