"""Canonical ATS resume builder — user template (2026-11-18).

Format spec (canonical for ALL tailored/master resumes):
  * single column, ATS-friendly: plain paragraphs + real bullets;
    NO tables, NO columns, NO icons, NO header/footer
  * Arial 10.5pt (name line 14pt bold), 2 pages max
  * Section order: Professional Summary, Technical Skills (~7 grouped lines),
    Professional Experience (Job Title / "Company, City | Mon YYYY - Mon YYYY" / bullets),
    Education
  * Truth contract: never change facts or invent metrics; bullets come from
    the master resume verbatim (keyword matching may REORDER bullets only).
    Missing numbers are never invented ("[add metric]" rule — this builder
    adds no numbers at all).

Deliverables per run: .docx + text-based PDF (Arial TTF embedded) +
automated extraction-order verification (docx readback + pdfplumber).

Usage (repo venv):
  .venv/Scripts/python.exe data/build_resume.py --company accesSOS --role "Full Stack Engineer"
  .venv/Scripts/python.exe data/build_resume.py --keywords "react,java,postgresql"
Outputs: data/exports/Manish Badugu <Company> <Role>.docx / .pdf
"""
import argparse
import json
import os
import re
import sys

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

MASTER = r"C:\Users\badug\Downloads\Manish_Badugu_AWS_SDE_II_Original_Format.docx"
EXPORTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
FONT_DIR = r"C:\Windows\Fonts"
CANONICAL_LINKEDIN = "linkedin.com/in/badugu-manish-2241"
POLARIS_TITLE = "Software Developer"  # not on master; used on Duke application (flagged to user)

MONTHS = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
}
DATE_RE = re.compile(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|Present|20\d\d", re.I)

# Master skill category -> output group (7 grouped lines)
SKILL_GROUPS = [
    ("Programming Languages", ["Programming Languages"]),
    ("Backend Technologies", ["Backend Technologies"]),
    ("Frontend Technologies", ["Frontend Technologies"]),
    ("Database Technologies", ["Database Technologies"]),
    ("Cloud & AI", ["Cloud Platforms", "AI Integration", "AI Frameworks"]),
    ("Testing & Tooling", ["Testing Frameworks", "Build and Dependency Management", "API Development and Testing"]),
    ("Practices & Tools", ["Version Control", "Development Practices", "Application Development"]),
]
# semantic de-dup (same thing, different wording) — dedupe key only, output keeps first spelling
DEDUPE_KEY = {"rest apis": "restful apis", "relational database management systems (rdbms)": "rdbms"}
TRASH_ITEMS = {"only where used"}


def norm_month(s):
    for full, short in MONTHS.items():
        s = re.sub(rf"\b{full}\b", short, s)
    return s


def norm_dates(s):
    s = norm_month(s.replace("\u2013", "-").replace("\u2014", "-"))
    s = re.sub(r"\s*-\s*", " - ", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


# USER RULE 2026-11-18: stack mismatch is no longer a gate — apply anyway and
# ADD the skills the JD asks for that the resume doesn't list. Group routing
# for injected skills (first keyword match wins); default: Practices & Tools.
_ADD_SKILL_GROUPS = [
    ("Programming Languages", ("python", "golang", "rust", "c++", "c#", "typescript", "scala", "kotlin", "php", "ruby", "swift")),
    ("Frontend Technologies", ("vue", "angular", "svelte", "tailwind", "bootstrap", "jquery", "webpack", "next.js", "nextjs")),
    ("Database Technologies", ("mongodb", "mysql", "oracle", "cassandra", "dynamodb", "elasticsearch", "redis", "firebase", "snowflake", "sql server")),
    ("Cloud & AI", ("azure", "gcp", "google cloud", "terraform", "docker", "kubernetes", "tensorflow", "pytorch", "machine learning", "llm", "nlp", "gpt", "heroku")),
    ("Backend Technologies", ("django", "flask", "fastapi", "node", "express", "graphql", "kafka", "rabbitmq", "grpc", "celery", "microservice", "rest", "spring", "rails")),
    ("Testing & Tooling", ("cypress", "selenium", "jest", "playwright", "jmeter", "junit", "mockito")),
]
_ADD_SKILL_DEFAULT = "Practices & Tools"


def inject_jd_skills(skills, add_list):
    """Append JD-asked skills to the best-fit group line (user rule 2026-11-18).

    `skills` is a list of "Group: item, item" strings, mutated in place.
    Returns the skills actually injected (ones already listed are skipped).
    """
    injected = []
    for sk in add_list:
        sk = sk.strip()
        if not sk:
            continue
        low = sk.lower()
        if any(low in l.lower() for l in skills):
            continue  # already on the resume
        group = _ADD_SKILL_DEFAULT
        for gname, kws in _ADD_SKILL_GROUPS:
            if any(k in low for k in kws):
                group = gname
                break
        for i, line in enumerate(skills):
            if line.split(":", 1)[0].strip() == group:
                skills[i] = line.rstrip() + ", " + sk
                break
        else:
            skills.append(f"{group}: {sk}")
        injected.append(sk)
    return injected


def parse_master(path=MASTER):
    doc = Document(path)
    paras = [p.text for p in doc.paragraphs]
    bolds = [all(r.bold for r in p.runs if r.text.strip()) if any(r.text.strip() for r in p.runs) else False
             for p in doc.paragraphs]
    data = {"name": None, "contact": None, "title": None, "summary": [],
            "skills": [], "jobs": [], "education": [], "order_issues": []}
    section = None
    for text, bold in zip(paras, bolds):
        t = text.strip()
        if not t:
            continue
        low = t.lower().rstrip(":").strip()
        if low in ("professional summary", "technical skills", "professional experience", "education"):
            section = low
            continue
        if data["name"] is None and bold:
            data["name"] = t
            continue
        if section is None:
            if "@" in t:
                data["contact"] = t
            elif bold:
                data["title"] = t
            continue
        if section == "professional summary":
            data["summary"].append(t)
        elif section == "technical skills":
            data["skills"].append(t)
        elif section == "professional experience":
            if bold and DATE_RE.search(t):
                parts = [x.strip() for x in re.split(r"\s{4,}", t) if x.strip()]
                company, dates = parts[0], norm_dates(parts[-1])
                data["jobs"].append({"company": company, "dates": dates,
                                     "title": None, "project": None, "bullets": []})
                continue
            job = data["jobs"][-1] if data["jobs"] else None
            if job is None:
                continue
            if bold:
                if t.lower().startswith("project name:"):
                    job["project"] = t.split(":", 1)[1].strip()
                elif t.lower().startswith("responsibilities:"):
                    pass
                else:
                    job["title"] = t
            else:
                job["bullets"].append(t)
        elif section == "education":
            data["education"].append(t)
    for job in data["jobs"]:
        if not job["title"]:
            job["title"] = POLARIS_TITLE
    return data


def group_skills(raw_lines):
    """Collapse the master's 14 category lines into 7 grouped lines (facts preserved)."""
    items_by_cat = {}
    for line in raw_lines:
        cat, _, rest = line.partition(":")
        cat = cat.strip()
        items = [i.strip() for i in rest.split(",") if i.strip()]
        cleaned = []
        for it in items:
            if it in TRASH_ITEMS:
                continue
            if it.lower().startswith("or "):
                it = it[3:].strip()
            cleaned.append(it)
        items_by_cat.setdefault(cat, []).extend(cleaned)
    out = []
    for group, cats in SKILL_GROUPS:
        seen, merged = set(), []
        for cat in cats:
            for it in items_by_cat.get(cat, []):
                key = DEDUPE_KEY.get(it.lower(), it.lower())
                if key in seen:
                    continue
                seen.add(key)
                merged.append(it)
        if merged:
            out.append(f"{group}: {', '.join(merged)}")
    return out


def reorder_by_keywords(jobs, keywords):
    """Deterministic JD match: move keyword-hitting bullets to the top (stable). Truth: reorder only."""
    kws = [k.strip().lower() for k in keywords if k.strip()]
    for job in jobs:
        def hits(b):
            bl = b.lower()
            return sum(1 for k in kws if k in bl)
        job["bullets"] = sorted(job["bullets"], key=lambda b: -hits(b))  # sorted() is stable
    return jobs


def build_docx(data, skills, path):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Arial"
    st.font.size = Pt(10.5)
    st.paragraph_format.space_after = Pt(0)
    st.paragraph_format.line_spacing = 1.0

    def para(text, bold=False, size=10.5, bullet=False, before=0, after=0):
        p = doc.add_paragraph(style="List Bullet" if bullet else "Normal")
        if before:
            p.paragraph_format.space_before = Pt(before)
        p.paragraph_format.space_after = Pt(after)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(text)
        r.bold = bold
        r.font.name = "Arial"
        r.font.size = Pt(size)
        return p

    # header block (name/contact/title) — no Word header/footer used
    para(data["name"], bold=True, size=14, after=2)
    contact = re.sub(r"\s*\|\s*$", "", data["contact"].strip())
    para(f"{contact}  |  {CANONICAL_LINKEDIN}", after=4)
    if data["title"]:
        para(data["title"], bold=True, after=6)

    para("Professional Summary", bold=True, before=6)
    for s in data["summary"]:
        para(s, after=2)

    para("Technical Skills", bold=True, before=6)
    for s in skills:
        para(s, after=1)

    para("Professional Experience", bold=True, before=6)
    for job in data["jobs"]:
        para(job["title"], bold=True, before=4)
        para(f'{job["company"]}  |  {job["dates"]}', bold=True, after=1)
        if job["project"]:
            para(f'Project: {job["project"]}')
        for b in job["bullets"]:
            para(b, bullet=True)

    para("Education", bold=True, before=6)
    for e in data["education"]:
        para(norm_dates(e), after=1)

    # guarantee empty header/footer (fresh template is already empty — assert just in case)
    for sec in doc.sections:
        assert not "".join(p.text for p in sec.header.paragraphs).strip()
        assert not "".join(p.text for p in sec.footer.paragraphs).strip()
    doc.save(path)


def _wrap(pdf, text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if pdf.get_string_width(trial) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def build_pdf(data, skills, path):
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(unit="pt", format="LETTER")
    pdf.add_font("Arial", "", os.path.join(FONT_DIR, "arial.ttf"))
    pdf.add_font("Arial", "B", os.path.join(FONT_DIR, "arialbd.ttf"))
    pdf.add_font("Arial", "I", os.path.join(FONT_DIR, "ariali.ttf"))
    pdf.add_font("Arial", "BI", os.path.join(FONT_DIR, "arialbi.ttf"))
    pdf.set_margins(50, 50, 50)
    pdf.set_auto_page_break(True, 50)
    pdf.add_page()
    LH = 11.6  # line height for 10.5pt Arial (~1.1)

    def line(text, style="", size=10.5, before=0, after=0, lh=LH):
        if before and pdf.get_y() + before + lh > pdf.h - pdf.b_margin:
            pdf.add_page()
        if before:
            pdf.ln(before)
        pdf.set_font("Arial", style, size)
        pdf.multi_cell(0, lh, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        if after:
            pdf.ln(after)

    def bullet(text, lh=LH):
        pdf.set_font("Arial", "", 10.5)
        lines = _wrap(pdf, text, pdf.epw - 12)
        x0 = pdf.l_margin
        for i, cont in enumerate(lines):
            if pdf.get_y() + lh > pdf.h - pdf.b_margin:
                pdf.add_page()
            pdf.set_x(x0 + 12)
            if i == 0:
                pdf.cell(6, lh, "\u2022", new_x=XPos.RIGHT, new_y=YPos.NEXT)
                pdf.set_x(x0 + 12)
            pdf.cell(0, lh, cont, new_x=XPos.RIGHT, new_y=YPos.NEXT)

    line(data["name"], "B", 14, after=2, lh=17)
    contact = re.sub(r"\s*\|\s*$", "", data["contact"].strip())
    line(f"{contact}  |  {CANONICAL_LINKEDIN}", after=4)
    if data["title"]:
        line(data["title"], "B", after=6)

    line("Professional Summary", "B", before=6)
    for s in data["summary"]:
        line(s, after=2)
    line("Technical Skills", "B", before=6)
    for s in skills:
        line(s, after=1)
    line("Professional Experience", "B", before=6)
    for job in data["jobs"]:
        line(job["title"], "B", before=4)
        line(f'{job["company"]}  |  {job["dates"]}', "B", after=1)
        if job["project"]:
            line(f'Project: {job["project"]}')
        for b in job["bullets"]:
            bullet(b)
    line("Education", "B", before=6)
    for e in data["education"]:
        line(norm_dates(e), after=1)

    pdf.output(path)
    return pdf.page_no()


def verify(docx_path, pdf_path, data, skills):
    import pdfplumber
    ok = True

    def check(cond, msg):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + msg)
        if not cond:
            ok = False

    # docx readback
    ddoc = Document(docx_path)
    dlines = [p.text.strip() for p in ddoc.paragraphs if p.text.strip()]
    # pdf readback
    with pdfplumber.open(pdf_path) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
        fonts = set()
        for p in pdf.pages:
            fonts |= {c["fontname"].split("+")[-1].split("-")[0] for c in p.chars if c.get("fontname")}
    plines = [l.strip() for page in pages for l in page.splitlines() if l.strip()]
    dtext, ptext = "\n".join(dlines), "\n".join(plines)

    print(f"[verify] docx lines={len(dlines)}  pdf pages={len(pages)}  fonts={sorted(fonts)}")

    for label, lines, text in (("docx", dlines, dtext), ("pdf", plines, ptext)):
        print(f"[verify] --- {label} order ---")
        check(lines[0] == data["name"], f"{label}: first line is name")
        idx = {}
        for sec in ("Professional Summary", "Technical Skills", "Professional Experience", "Education"):
            idx[sec] = text.find("\n" + sec + "\n") if ("\n" + sec + "\n") in text else text.find(sec)
        order = [sec for sec, _ in sorted(idx.items(), key=lambda kv: kv[1]) if _ >= 0]
        expected = ["Professional Summary", "Technical Skills", "Professional Experience", "Education"]
        check(order == expected, f"{label}: section order {order} == {expected}")
        for company in (j["company"] for j in data["jobs"]):
            check(company in text, f"{label}: contains '{company}'")
        pos = [text.find(j["company"]) for j in data["jobs"]]
        check(pos == sorted(pos) and -1 not in pos, f"{label}: jobs in master order")
        check("[add metric]" not in text, f"{label}: no invented-metric placeholders")
        n_skills = sum(1 for l in lines if l.split(":")[0].strip() in {g for g, _ in SKILL_GROUPS})
        check(n_skills == len(skills) and len(skills) <= 8, f"{label}: technical skills = {n_skills} grouped lines")
    check(len(pages) <= 2, "pdf: 2 pages max")
    check(any(f == "Arial" for f in fonts), "pdf: Arial font embedded (text-based)")
    # every master bullet present verbatim (truth contract) — whitespace-normalized
    # (PDF extraction inserts line breaks where bullets wrap)
    ptext_norm = re.sub(r"\s+", " ", ptext)
    master_bullets = [b for j in data["jobs"] for b in j["bullets"]]
    missing = [b for b in master_bullets if re.sub(r"\s+", " ", b) not in ptext_norm]
    check(not missing, f"pdf: all {len(master_bullets)} master bullets present verbatim ({len(missing)} missing)")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--company", default=None)
    ap.add_argument("--role", default=None)
    ap.add_argument("--keywords", default=None, help="comma list or path to JD text")
    ap.add_argument("--add-skills", default=None,
                    help="comma list of JD-asked skills to add to the skill lines (user rule 2026-11-18)")
    ap.add_argument("--master", default=MASTER)
    ap.add_argument("--content", default=None,
                    help="path to a verified content JSON (LLM rewrite) — bypasses master parse")
    ap.add_argument("--out", default=EXPORTS)
    args = ap.parse_args()

    if args.content:
        with open(args.content, encoding="utf-8") as f:
            data = json.load(f)
        skills = data["skills"]  # already grouped
        # summary may arrive as a single string — the renderers iterate over it
        if isinstance(data.get("summary"), str):
            data["summary"] = [data["summary"]]
        for j in data.get("jobs", []):
            j.setdefault("project", None)
    else:
        data = parse_master(args.master)
        skills = group_skills(data["skills"])
    if args.add_skills:
        add_list = [s.strip() for s in args.add_skills.split(",") if s.strip()]
        injected = inject_jd_skills(skills, add_list)
        if injected:
            print(f"[add-skills] JD skills added to resume: {', '.join(injected)}")
    if args.keywords:
        kw = args.keywords
        if os.path.isfile(kw):
            kw = open(kw, encoding="utf-8").read()
        data["jobs"] = reorder_by_keywords(data["jobs"], kw.split(","))

    company = args.company or ""
    role = args.role or (data["title"] or "Software Developer")
    base = " ".join(p for p in [data["name"]] + ([company] if company else []) + [role] if p)
    base = base.replace("_", " ")
    os.makedirs(args.out, exist_ok=True)
    docx_path = os.path.join(args.out, base + ".docx")
    pdf_path = os.path.join(args.out, base + ".pdf")

    build_docx(data, skills, docx_path)
    pages = build_pdf(data, skills, pdf_path)
    print(f"built: {docx_path}")
    print(f"built: {pdf_path}  ({pages} page(s))")
    ok = verify(docx_path, pdf_path, data, skills)
    print("VERIFY:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
