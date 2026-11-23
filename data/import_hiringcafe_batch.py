"""Import hiring.cafe ssrHits batch into jobflow.db using the app's exact key logic.

Usage: python data/import_hiringcafe_batch.py <new_hits.json>
- unique_key = sha1('hiringcafe|' + apply_url)   (== ingestion.job_unique_key)
- norm_key   = sha1(slug(company)|slug(title)|slug(location)) (== job_norm_key)
- skips any hit whose unique_key or norm_key already exists
- writes data/hc_batch_v5.json sidecar: {db_id: v5 structured data} for the pre-screen
"""
import hashlib
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone

REPO = r"C:\Users\badug\jobflow"
DB = REPO + r"\data\jobflow.db"
SOURCE = "hiringcafe"

def slug(text):
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())

def as_list(v):
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]

def parse_yoe(v):
    if v is None:
        return None
    try:
        s = str(v).strip()
        m = re.search(r"(\d+(?:\.\d+)?)", s)
        return float(m.group(1)) if m else None
    except Exception:
        return None

def main(path):
    hits = json.load(open(path, encoding="utf-8"))
    con = sqlite3.connect(DB)
    have_uk = {r[0] for r in con.execute("select unique_key from jobs")}
    have_nk = {r[0] for r in con.execute("select norm_key from jobs where norm_key != ''")}
    have_url = {r[0].lower().rstrip("/") for r in con.execute("select apply_url from jobs where apply_url is not null")}

    now = datetime.now(timezone.utc).isoformat()
    inserted, skipped, v5_sidecar = 0, 0, {}

    for h in hits:
        v5 = h.get("v5_processed_job_data") or {}
        url = (h.get("apply_url") or "").strip()
        if not url:
            skipped += 1
            continue
        title = (v5.get("core_job_title") or "").strip()
        if not title:
            skipped += 1
            continue
        org = (h.get("attributed_org") or {}) or {}
        company = (org.get("name") or v5.get("company_name") or "").strip()
        if not company:
            skipped += 1
            continue

        if url.lower().rstrip("/") in have_url:
            skipped += 1
            continue

        countries = as_list(v5.get("workplace_countries"))
        states = as_list(v5.get("workplace_states"))
        cities = as_list(v5.get("workplace_cities"))
        wtype = (v5.get("workplace_type") or "").lower()
        remote = "remote" in wtype or bool(v5.get("is_workplace_worldwide_ok"))

        if remote:
            loc = "Remote"
        elif cities:
            loc = ", ".join(str(c) for c in cities[:2])
            if states:
                loc += ", " + str(states[0])
            if countries:
                loc += ", " + str(countries[0])
        else:
            loc = ", ".join(str(c) for c in (countries or [""]))
        loc = loc.strip(", ") or None

        uk = hashlib.sha1(f"{SOURCE}|{url}".encode("utf-8")).hexdigest()
        nk = hashlib.sha1(f"{slug(company)}|{slug(title)}|{slug(loc)}".encode("utf-8")).hexdigest()
        if uk in have_uk or nk in have_nk:
            skipped += 1
            continue

        visa = v5.get("visa_sponsorship")
        visa_val = 1 if visa == "Yes" else (0 if visa == "No" else None)

        row = (
            title[:400], company[:300],
            (org.get("website") or v5.get("company_website") or "")[:500] or None,
            (loc or "")[:400] or None,
            json.dumps(countries), 1 if remote else 0, visa_val,
            json.dumps(as_list(v5.get("commitment"))), parse_yoe(v5.get("min_industry_and_role_yoe")),
            None, None, 'USD',
            url[:1000], SOURCE, str(h.get("objectID") or "")[:120],
            now, 1, "[]", uk, now,
        )
        cur = con.execute(
            """insert into jobs (title, company, company_website, location, countries_json, remote,
               visa_sponsorship, commitment_json, yoe, salary_min, salary_max, salary_currency,
               apply_url, source, hiringcafe_id, indexed_at, passes_filters, filter_reasons_json,
               unique_key, fetched_at)
               values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            row,
        )
        have_uk.add(uk)
        have_nk.add(nk)
        have_url.add(url.lower().rstrip("/"))
        v5_sidecar[str(cur.lastrowid)] = {
            "title": title, "company": company, "url": url,
            "security_clearance": v5.get("security_clearance"),
            "visa_sponsorship": visa, "min_yoe": v5.get("min_industry_and_role_yoe"),
            "workplace_countries": countries, "workplace_states": states, "workplace_cities": cities,
            "workplace_type": v5.get("workplace_type"), "commitment": v5.get("commitment"),
            "technical_tools": v5.get("technical_tools"), "core_job_title": v5.get("core_job_title"),
            "estimated_publish_date": v5.get("estimated_publish_date"),
            "bachelors_degree_requirement": v5.get("bachelors_degree_requirement"),
            "seniority_level": v5.get("seniority_level"),
        }
        inserted += 1

    con.commit()
    json.dump(v5_sidecar, open(REPO + r"\data\hc_batch_v5.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"inserted={inserted} skipped={skipped} total={len(hits)}")
    con.close()

if __name__ == "__main__":
    main(sys.argv[1])
