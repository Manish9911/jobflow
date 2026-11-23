"""build_content.py — deterministic 2-page resume content from the master (no LLM).

Truth contract: bullets are a VERBATIM subset of the master. Selection per job:
JD-keyword-hitting bullets first (stable original order), then earliest remaining
bullets to fill the per-job budget. Budgets sized to fit 2 pages at Arial 10.5pt.

Usage:
  python data/build_content.py --keywords "react,postgresql,sql,..." [--out path]
  python data/build_resume.py --content <out> --company X --role Y [--keywords ...]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_resume import parse_master, group_skills  # noqa: E402

BUDGETS = {"Verizon": 10, "Equifax": 9, "Polaris": 6}


def select(bullets, keywords, budget):
    kws = [k.strip().lower() for k in keywords if k.strip()]

    def hits(b):
        bl = b.lower()
        return sum(1 for k in kws if k in bl)

    hit = [b for b in bullets if hits(b) > 0]
    rest = [b for b in bullets if hits(b) == 0]
    return (hit + rest)[:budget]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keywords", default="")
    ap.add_argument("--title", default="Software Development Engineer",
                    help="target role shown under the name (header line only)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   "exports", "deterministic_content.json"))
    ap.add_argument("--budgets", default=None,
                    help="override per-job budgets as V,E,P (e.g. '8,7,5') — "
                         "used to fit WHY/WHAT/PROOF bullets inside 2 pages")
    args = ap.parse_args()

    budgets = dict(BUDGETS)
    if args.budgets:
        parts = [int(x) for x in args.budgets.split(",") if x.strip() != ""]
        if len(parts) == 3:
            budgets = {"Verizon": parts[0], "Equifax": parts[1], "Polaris": parts[2]}

    m = parse_master()
    kws = args.keywords.split(",")
    jobs = []
    for j in m["jobs"]:
        co = j["company"].split(",")[0].split()[0].strip()
        budget = budgets.get(co, 8)
        jobs.append({
            "title": j["title"],
            "company": j["company"],
            "dates": j["dates"],
            "project": j["project"],
            "bullets": select(j["bullets"], kws, budget),
        })
    summary = m["summary"] if isinstance(m["summary"], list) else [m["summary"]]
    content = {
        "name": m["name"],
        "contact": m["contact"],
        "title": args.title,
        "summary": summary,
        "skills": group_skills(m["skills"]),
        "jobs": jobs,
        "education": m["education"],
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=1)
    print("wrote", args.out)
    print("bullets:", [len(j["bullets"]) for j in jobs])
    print("skill lines:", len(content["skills"]))
    print("summary chars:", sum(len(s) for s in summary))


if __name__ == "__main__":
    main()
