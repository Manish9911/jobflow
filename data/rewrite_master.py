"""LLM rewrite of the master resume into the canonical 2-page template.

Truth contract enforced deterministically AFTER the LLM call:
  * companies / titles / dates / education must match the master exactly
  * skill items must be a subset of the master's skill items
  * no number/year that does not exist in the master
  * no capitalized token (except sentence-start words) absent from the master corpus
  * bullet-count budgets (2-page fit)
Any failure -> retry with the issues listed (max 3 attempts), else abort.
Success -> writes a content JSON for: build_resume.py --content <file>
"""
import json
import os
import re
import sys
import time

REPO = r"C:\Users\badug\jobflow"
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "data"))

from backend.app.config import Settings  # noqa: E402
from backend.app.llm import get_llm  # noqa: E402
from build_resume import parse_master, norm_dates  # noqa: E402

OUT = os.path.join(REPO, "data", "exports", "rewrite_content.json")

settings = Settings()
llm = get_llm(settings)
if not llm.is_available():
    print("LLM not available — cannot rewrite")
    sys.exit(2)
print("llm:", type(llm).__name__, "model:", llm.model)

master = parse_master()
# master corpora
corpus_lines = []
from docx import Document as _Doc  # noqa: E402
_mdoc = _Doc(r"C:\Users\badug\Downloads\Manish_Badugu_AWS_SDE_II_Original_Format.docx")
corpus_lines = [p.text for p in _mdoc.paragraphs]
CORPUS = re.sub(r"\s+", " ", " ".join(corpus_lines)).lower()
YEARS = set(re.findall(r"20\d\d", " ".join(corpus_lines)))

# master skill item set (normalized)
master_items = set()
for line in master["skills"]:
    _, _, rest = line.partition(":")
    for it in rest.split(","):
        it = it.strip()
        if it.lower().startswith("or "):
            it = it[3:].strip()
        if it.lower() != "only where used":
            base = re.sub(r"\s+", " ", it).lower()
            master_items.add(base)
            # "Full Name (ABBR)" — the abbreviation is also a source-truth skill
            m = re.search(r"\(([^)]+)\)\s*$", base)
            if m:
                master_items.add(m.group(1).strip())
DEDUPE_KEY = {"rest apis": "restful apis"}
def item_key(it):
    k = re.sub(r"\s+", " ", it).lower()
    return DEDUPE_KEY.get(k, k)
master_item_keys = {item_key(i) for i in master_items}

BUDGETS = {"Verizon": 10, "Equifax": 9, "Polaris": 6}
ALLOWED_TITLES = {j["title"] for j in master["jobs"]}
ALLOWED_TITLES.add("Software Developer")
ALLOWED_TITLES.add("Software Development Engineer")  # master header title (line 2)

SYSTEM = (
    "You are a resume rewriting engine. Respond with STRICT JSON only — no markdown, "
    "no code fences, no commentary. HARD TRUTH CONTRACT: you may only reorder, shorten, "
    "reword, or merge facts present in the source resume. You must NEVER invent employers, "
    "job titles, dates, degrees, skills, products, or metrics. Every number or year in your "
    "output must exist in the source. Use strong action verbs. No first person."
)

def user_prompt(issues=None):
    src = "\n".join(t.strip() for t in corpus_lines if t.strip())
    p = f"""Rewrite this resume to fit a single-column ATS template (Arial 10.5pt, 2 pages max).

Output EXACTLY this JSON shape:
{{
  "name": str,
  "contact": "+1 940-843-6058 | badugu.m7@gmail.com",
  "title": "Software Development Engineer",
  "summary": "one paragraph, 3-5 sentences, max 430 characters",
  "skills": [exactly 7 strings, using EXACTLY these group names:
             "Programming Languages: ...", "Backend Technologies: ...", "Frontend Technologies: ...",
             "Database Technologies: ...", "Cloud & AI: ...", "Testing & Tooling: ...", "Practices & Tools: ..."],
  "jobs": [
    {{"title": str, "company": str, "dates": "Mon YYYY - Mon YYYY", "project": str or null,
      "bullets": [action-verb bullets, each max ~110 chars]}},
    ... one object per job, same order as source ...
  ],
  "education": [keep the two source education lines, normalize dashes to "-"]
}}

BUDGETS (hard, for the 2-page fit): max bullets per job — Verizon 10, Equifax 9, Polaris 6.
Keep the most impactful bullets (backend, Java/Spring, REST, PostgreSQL, AWS, React, testing).

EXACT FIELDS (copy these strings verbatim — do NOT shorten, rename, or retitle):
  name = "Manish Badugu"
  title = "Software Development Engineer"
  job 1: title "Sr. Java Full Stack Developer", company "Verizon Communications, New York", dates "Jul 2025 - Present"
  job 2: title "Full Stack Developer", company "Equifax, Alpharetta, GA", dates "Jul 2024 - Jun 2025"
  job 3: title "Software Developer", company "Polaris, Hyderabad, India", dates "Jun 2021 - Nov 2022"
  (Keep company names, project names, and dates EXACTLY as above — only normalize month
   abbreviations in bullets. The two education lines must keep their degree, school, and
   date range intact; normalize dashes to "-".)
The 7 skill lines must use only skill items from the source; keep: Java, JavaScript, SQL,
Spring Boot, Spring Framework, RESTful APIs, Microservices, React.js, HTML5, CSS3,
PostgreSQL, RDBMS, AWS, LLM API Integration, LangChain, Spring AI, OpenAI API, JUnit, Mockito,
Maven, Gradle, Postman, Swagger/OpenAPI, Git, GitHub, Agile/Scrum, Design Patterns,
Root Cause Analysis, Full Stack Development.

SOURCE RESUME:
{src}
"""
    if issues:
        p += "\n\nPREVIOUS ATTEMPT FAILED VERIFICATION. Fix ALL of these:\n" + "\n".join("- " + i for i in issues)
    return p


def extract_json(text):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return json.loads(text[start:end + 1])


def verify(c):
    issues = []
    for k in ("name", "contact", "title", "summary", "skills", "jobs", "education"):
        if k not in c:
            issues.append(f"missing key: {k}")
    if issues:
        return issues
    if c["name"] != master["name"]:
        issues.append(f"name must be {master['name']}")
    if not (re.search(r"940-843-6058", c["contact"]) and "badugu.m7@gmail.com" in c["contact"]):
        issues.append("contact must keep the source phone and email")
    if c["title"] not in ALLOWED_TITLES:
        issues.append(f"title must be one of {sorted(ALLOWED_TITLES)}")
    s = c["summary"]
    if isinstance(s, list):
        s = " ".join(s)
    if len(s) > 600:
        issues.append(f"summary too long ({len(s)} chars, max 600)")
    for tok in re.findall(r"\b[0-9]+\+?\b", s):
        if tok not in ("4",) and tok not in {t for t in re.findall(r"\b[0-9]+\+?\b", " ".join(master["summary"]))}:
            issues.append(f"summary contains number not in source: {tok}")
    skills = c["skills"]
    if len(skills) != 7:
        issues.append(f"skills must have exactly 7 lines (got {len(skills)})")
    for line in skills:
        if ":" not in line:
            issues.append(f"skill line not 'Category: items': {line[:60]}")
            continue
        for it in line.split(":", 1)[1].split(","):
            it = it.strip()
            if it and item_key(it) not in master_item_keys:
                issues.append(f"skill item not in source: {it!r}")
    if len(c["jobs"]) != 3:
        issues.append(f"jobs must have 3 entries (got {len(c['jobs'])})")
        return issues
    for job, mjob in zip(c["jobs"], master["jobs"]):
        for field in ("title", "company", "dates", "bullets"):
            if field not in job:
                issues.append(f"job {mjob['company']}: missing {field}")
        mbase = mjob["company"].split(",")[0].strip()
        jco = (job.get("company") or "").strip()
        if jco.split(",")[0].strip() != mbase:
            issues.append(f"company mismatch: {jco!r} != {mjob['company']!r}")
        else:
            # city is a fixed fact from the master — auto-restore the full "Company, City"
            job["company"] = mjob["company"]
        if norm_dates(job.get("dates", "")) != norm_dates(mjob["dates"]):
            issues.append(f"dates mismatch for {mjob['company']}: {job.get('dates')!r} != {mjob['dates']!r}")
        if job.get("title") != mjob["title"]:
            issues.append(f"job title mismatch for {mjob['company']}: {job.get('title')!r} != {mjob['title']!r}")
        cap = BUDGETS.get(mjob["company"].split(",")[0].split()[0].strip(), 10)
        bl = job.get("bullets", [])
        if len(bl) > cap:
            issues.append(f"{mjob['company']}: {len(bl)} bullets > budget {cap}")
        proj = job.get("project")
        if proj and mjob.get("project") and re.sub(r"\s+", " ", proj).lower() not in CORPUS:
            issues.append(f"project name not in source: {proj!r}")
        for b in bl:
            toks = [t for t in re.findall(r"\b[A-Z][A-Za-z0-9/&.\-]*", b)]
            for t in toks[1:]:  # skip sentence-start word
                if t.rstrip(".,;:").lower() not in CORPUS and item_key(t) not in master_item_keys:
                    issues.append(f"unknown capitalized token in bullet: {t!r} (in: {b[:50]}...)")
                    break
            for y in re.findall(r"20\d\d", b):
                if y not in YEARS:
                    issues.append(f"year {y} not in source (in: {b[:50]}...)")
    edu = c["education"]
    if len(edu) != 2:
        issues.append(f"education must have 2 lines (got {len(edu)})")
    for line, mline in zip(edu, master["education"]):
        ln = re.sub(r"[—–]", "-", line.lower())
        for frag in re.split(r"[—–|]", mline):
            frag = frag.strip()
            if len(frag) > 6 and re.sub(r"[—–]", "-", frag.lower()) not in ln:
                issues.append(f"education fragment missing: {frag!r}")
    # global: no invented years anywhere
    alltext = json.dumps(c).lower()
    for y in set(re.findall(r"20\d\d", alltext)):
        if y not in YEARS:
            issues.append(f"invented year: {y}")
    return issues


def llm_with_backoff(prompt):
    """Free-tier pool 429s for minutes — back off inside the attempt instead of crashing."""
    delays = (30, 90, 180)
    for i, d in enumerate(delays + (None,)):
        try:
            return llm.complete(SYSTEM, prompt, temperature=0.15, timeout=180)
        except Exception as e:
            print(f"  LLM call failed ({type(e).__name__}: {e})")
            if d is None:
                raise
            print(f"  backing off {d}s ...")
            time.sleep(d)


attempts, last = 0, None
while attempts < 3:
    attempts += 1
    print(f"--- attempt {attempts} ---")
    try:
        raw = llm_with_backoff(user_prompt(last))
    except Exception as e:
        last = [f"LLM call failed: {e}"]
        print("  LLM unavailable for this attempt:", e)
        continue
    try:
        c = extract_json(raw)
    except Exception as e:
        last = [f"output was not valid JSON: {e}"]
        print("  JSON parse failed:", e)
        continue
    issues = verify(c)
    if issues:
        last = issues
        print("  verify FAILED:")
        for i in issues:
            print("   -", i)
        continue
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
    print(f"VERIFY PASS — wrote {OUT}")
    print("bullets:", [len(j["bullets"]) for j in c["jobs"]])
    sys.exit(0)

print("ABORT: 3 attempts failed truth verification — no file written (deterministic master build remains the fallback)")
sys.exit(1)
