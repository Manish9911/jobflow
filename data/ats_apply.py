#!/usr/bin/env python3
"""Generic ATS apply driver — one reusable script for ANY careers site.

User rules encoded:
- Visible local Chrome via CDP (port 9334, badugu.m7@gmail.com profile), never headless.
- DRY-RUN by default: fills everything, stops before the real submit button.
  Pass --submit to actually submit.
- Resume autofill: if the form has a resume/CV file input, upload the tailored
  PDF FIRST so the ATS can prefill (user rule 2026-11-11); then fill whatever
  the autofill missed.
- EEO/diversity questions: ALWAYS the negative answer. Never blank, never Yes.
- Relocation: No. ITAR: No. Work authorization: Yes. Sponsorship: Yes.
- Security clearance question anywhere on the form (or "must have clearance"
  in the page) => status rejected_clearance, fill nothing, stop (user rule).
- reCAPTCHA / Turnstile / human-verification wall => needs_manual + evidence +
  a "CAPTCHA FLAG" print line so the caller notifies the user immediately.
- Unknown fields: left blank and reported — never invent data.

Output: prints a JSON result on the last line:
  {"status": submitted|dry_run_stopped|blocked_recaptcha|blocked_botwall|
             rejected_clearance|needs_manual,
   "filled": [...], "empty": [...], "error": str|null, "evidence": path}

Usage:
  python data/ats_apply.py --url <job-or-apply-url> --resume <tailored.pdf> \
      --company "Acme" [--role "SDE"] [--submit] [--answers answers.json] \
      [--evidence-dir data/evidence]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

CDP = "http://127.0.0.1:9334"  # user's VISIBLE Chrome (Default profile) — the one that passes walls

DEFAULT_ANSWERS = {
    "first_name": "Manish",
    "last_name": "Badugu",
    "full_name": "Manish Badugu",
    "email": "badugu.m7@gmail.com",
    "phone": "+1 940-843-6058",
    "linkedin": "https://www.linkedin.com/in/badugu-manish-2241/",
    "github": "https://github.com/Manish9911",
    "street": "Almond Willow CV",
    "city": "Collierville",
    "state": "TN",
    "zip": "38017",
    "country": "United States",
    "salary": "Open to discussion — market rate",
}

# keyword (in label text) -> answer key. FIRST match wins, so most-specific first.
LABEL_KEYS = [
    (r"first name|given name|forename", "first_name"),
    (r"last name|surname|family name", "last_name"),
    (r"full name|your name|legal name", "full_name"),
    (r"phone|mobile|cell", "phone"),
    (r"linkedin", "linkedin"),
    (r"github", "github"),
    (r"zip|postal|pin code", "zip"),
    (r"\bstate\b", "state"),
    (r"city", "city"),
    (r"street|address line|residential address|address", "street"),
    (r"country|nationality", "country"),
    (r"salary|compensation", "salary"),
    (r"email|e-mail", "email"),
    (r"^name$|name", "full_name"),
]

# radio/checkbox label rules (label text -> choice)
CHOICE_RULES = [
    (r"security clearance|clearance level|top secret|secret\b", "CLEARANCE_GATE"),
    (r"relocat", "No"),
    (r"itar|export control", "No"),
    (r"authorized to work|work in the united states|legally authorized|work authoriz", "Yes"),
    (r"visa sponsorship|need (visa )?sponsorship|sponsorship", "Yes"),
    (r"veteran", "No"),
    (r"disabilit|neurodiverse|accommodat", "No"),
    (r"lgbt|gay|lesbian|transgender", "No"),
    (r"hispanic|latino|latina", "No"),
    (r"protected class|under-represent|under represent|minority|diversity|diverse", "No"),
    (r"veterans of the us|military service", "No"),
    (r"caregiver|carer", "No"),
    (r"part of a protected|identity|gender identity|sexual orientation", "No"),
    (r"notice period", "1 month"),
]

STATE_ALIASES = {"tennessee": "TN"}
COUNTRY_ALIASES = {"usa": "United States", "united states of america": "United States"}


def field_label(page, el) -> str:
    """Best-effort label text for an input/select/textarea."""
    try:
        info = page.evaluate(
            """el => {
                let out = [];
                const id = el.id ? el.id.split(/[^a-z0-9]/i)[0] : '';
                if (el.labels && el.labels.length) out.push([...el.labels].map(l => l.innerText).join(' '));
                if (el.getAttribute('aria-label')) out.push(el.getAttribute('aria-label'));
                if (el.placeholder) out.push(el.placeholder);
                if (el.name) out.push(el.name);
                if (id) {
                    const lab = document.querySelector('label[for*="' + id + '"]');
                    if (lab) out.push(lab.innerText);
                    const p = el.closest('[data-field-name]') || el.closest('.form-field, .field, .c-field, [class*="question"]');
                    if (p) {
                        const h = p.querySelector('label, .question-text, [class*="label"], h3, h4, .question');
                        if (h) out.push(h.innerText);
                    }
                }
                return out.filter(Boolean).join(' | ');
            }""",
            el,
        )
        return (info or "").strip().lower()
    except Exception:
        return ""


def visible(page) -> bool:
    try:
        return page.is_visible(timeout=500)
    except Exception:
        return False


def detect_blockers(page) -> str | None:
    try:
        txt = page.evaluate("() => (document.body ? document.body.innerText : '')") or ""
    except Exception:
        txt = ""
    if re.search(r"verify you are human|confirm you're human|verify you're human", txt, re.I):
        return "blocked_recaptcha"
    for f in page.query_selector_all("iframe"):
        try:
            src = f.get_attribute("src") or ""
        except Exception:
            src = ""
        if re.search(r"recaptcha|g-recaptcha|challenges\.cloudflare|turnstile|hcaptcha|arkoselabs", src, re.I):
            return "blocked_recaptcha"
    if re.search(r"are you a robot|unusual traffic|access denied|waf|captcha required", txt, re.I):
        return "blocked_recaptcha"
    return None


def clearance_gate(page) -> bool:
    try:
        txt = page.evaluate("() => (document.body ? document.body.innerText : '')") or ""
    except Exception:
        txt = ""
    return bool(re.search(r"security clearance|clearance eligibility|must hold (a )?(active )?clearance|top secret|ts/sci", txt, re.I))


def click_apply(page) -> bool:
    """If the page is a job-posting page, click the Apply button/link."""
    for sel in [
        "button:has-text('Apply')", "a:has-text('Apply now')", "button:has-text('Apply now')",
        "a:has-text('Apply')", "input[value='Apply']",
    ]:
        for el in page.query_selector_all(sel):
            if not visible(page_el := el):
                continue
            try:
                el.click(timeout=4000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                time.sleep(2.5)
                return True
            except Exception:
                continue
    return False


def fill_choices(page, report) -> str | None:
    """Handle radios/checkboxes per CHOICE_RULES. Returns 'rejected_clearance' if a clearance question exists."""
    clearance = False
    try:
        groups = page.query_selector_all("input[type=radio], input[type=checkbox]")
    except Exception:
        groups = []
    for el in groups:
        if not visible(el):
            continue
        label = field_label(page, el)
        if not label:
            continue
        for pat, choice in CHOICE_RULES:
            if re.search(pat, label, re.I):
                if choice == "CLEARANCE_GATE":
                    clearance = True
                target = "Yes" if choice == "Yes" else choice
                # click the option in this group matching the target choice
                name = el.get_attribute("name") or ""
                opts = page.query_selector_all(f'input[type=radio][name="{name}"]') if name else []
                if not opts:
                    opts = [el]
                for opt in opts:
                    try:
                        lab = field_label(page, opt)
                    except Exception:
                        lab = ""
                    if re.fullmatch(rf"\s*{target}\s*", lab, re.I) or re.search(rf"\b{target.lower()}\b", lab):
                        try:
                            if opt.is_checked():
                                continue
                            opt.check(timeout=2500)
                            report["filled"].append(f"choice: {label[:60]} -> {target}")
                        except Exception:
                            pass
                        break
                else:
                    report["empty"].append(f"choice: {label[:60]} (no '{target}' option)")
                break
    return "rejected_clearance" if clearance else None


def fill_fields(page, answers, report) -> None:
    try:
        els = page.query_selector_all("input:not([type=hidden]):not([type=radio]):not([type=checkbox]):not([type=file]), select, textarea")
    except Exception:
        els = []
    for el in els:
        if not visible(el):
            continue
        tag = el.evaluate("el => el.tagName.toLowerCase()")
        ftype = (el.get_attribute("type") or "").lower()
        label = field_label(page, el)
        # resume/attachment inputs handled separately
        if ftype == "file" or re.search(r"resume|cv|attach|upload", label):
            continue
        key = None
        for pat, k in LABEL_KEYS:
            if re.search(pat, label, re.I):
                key = k
                break
        if not key:
            continue
        value = answers[key]
        if tag == "select":
            opts = el.query_selector_all("option")
            ok = False
            for opt in opts:
                t = (opt.inner_text() or "").strip()
                if t.lower() == value.lower() or t.lower() == value.lower().replace(" ", ""):
                    el.select_option(label=t, timeout=2500)
                    report["filled"].append(f"{key} (select)")
                    ok = True
                    break
            if not ok:
                # try first-word / alias match
                for opt in opts:
                    t = (opt.inner_text() or "").strip()
                    if t.lower() in (STATE_ALIASES.get(value.lower(), value.lower()),
                                     COUNTRY_ALIASES.get(value.lower(), value.lower())):
                        el.select_option(label=t, timeout=2500)
                        report["filled"].append(f"{key} (select alias '{t}')")
                        ok = True
                        break
            if not ok:
                report["empty"].append(f"{key} (no matching option)")
            continue
        try:
            cur = el.input_value(timeout=800)
        except Exception:
            cur = ""
        if cur:  # autofill already filled it — trust the ATS
            continue
        try:
            el.fill(value, timeout=2500)
            report["filled"].append(f"{key} ({label[:40] or tag})")
        except Exception:
            try:
                el.type(value, timeout=2500)
                report["filled"].append(f"{key} (typed)")
            except Exception:
                report["empty"].append(f"{key} ({label[:40] or tag})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--resume", required=True)
    ap.add_argument("--company", default="")
    ap.add_argument("--role", default="")
    ap.add_argument("--submit", action="store_true", help="actually click submit (default: dry-run)")
    ap.add_argument("--answers", default=None, help="JSON file overriding DEFAULT_ANSWERS")
    ap.add_argument("--evidence-dir", default="data/evidence")
    args = ap.parse_args()

    answers = dict(DEFAULT_ANSWERS)
    if args.answers and os.path.isfile(args.answers):
        answers.update(json.load(open(args.answers, encoding="utf-8")))

    result = {"status": "needs_manual", "filled": [], "empty": [], "error": None,
              "evidence": None, "company": args.company, "role": args.role, "url": args.url}
    report = result

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP)
        except Exception as e:
            result["error"] = f"CDP connect failed: {e}"
            print(json.dumps(result))
            return 2
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        try:
            page.goto(args.url, timeout=45000)
            page.wait_for_load_state("domcontentloaded", timeout=30000)
            time.sleep(2)

            # 0) clearance gate — before touching anything
            if clearance_gate(page):
                result["status"] = "rejected_clearance"
                result["error"] = "form/JD asks about security clearance — rejected, nothing filled"
                dump_evidence(page, args, result)
                print(json.dumps(result))
                return 0

            # 1) get to the form (posting page -> apply page)
            for _ in range(2):
                if page.query_selector_all("input[type=file]"):
                    break
                if not click_apply(page):
                    break

            # 2) blocker detection (recaptcha / bot wall)
            blk = detect_blockers(page)
            if blk:
                result["status"] = blk
                result["error"] = "human-verification wall — user must clear manually"
                dump_evidence(page, args, result)
                print("CAPTCHA FLAG: user must clear this manually:", args.url)
                print(json.dumps(result))
                return 0

            # 3) resume upload first (lets the ATS autofill) — first file input wins
            for fi in page.query_selector_all("input[type=file]"):
                try:
                    fi.set_files(os.path.abspath(args.resume), timeout=15000)
                    report["filled"].append("resume upload")
                    break
                except Exception:
                    continue
            time.sleep(4)  # let the ATS parse + autofill

            # 3b) a new tab may have opened (some ATSes) — re-target the form page
            pages = ctx.pages
            if len(pages) > 1:
                for pg in pages[1:]:
                    if pg.query_selector_all("input:not([type=hidden])"):
                        page = pg
                        break

            # 4) choices (radios/checkboxes) — includes clearance gate on the form
            gate = fill_choices(page, report)
            if gate:
                result["status"] = gate
                result["error"] = "form asks about security clearance — rejected"
                dump_evidence(page, args, result)
                print(json.dumps(result))
                return 0

            # 5) text fields / selects
            fill_fields(page, answers, report)

            # 6) submit or dry-run
            if args.submit:
                clicked = False
                for sel in ["button[type=submit]:has-text('Submit')", "button:has-text('Submit application')",
                            "button[type=submit]", "button:has-text('Submit')"]:
                    for el in page.query_selector_all(sel):
                        if visible(el):
                            try:
                                el.click(timeout=5000)
                                clicked = True
                                break
                            except Exception:
                                continue
                    if clicked:
                        break
                if not clicked:
                    result["status"] = "needs_manual"
                    result["error"] = "no submit button found"
                else:
                    time.sleep(6)
                    ok = False
                    try:
                        url = page.url.lower()
                        txt = (page.evaluate("() => document.body.innerText") or "")
                        ok = bool(re.search(r"confirm|thank|success|submitted|received", url + " " + txt, re.I))
                    except Exception:
                        pass
                    result["status"] = "submitted" if ok else "needs_manual"
                    if not ok:
                        result["error"] = "no confirmation detected after submit — verify manually"
            else:
                result["status"] = "dry_run_stopped"

            dump_evidence(page, args, result)
            print(json.dumps(result))
            return 0
        except Exception as e:
            result["error"] = str(e)[:500]
            try:
                dump_evidence(page, args, result)
            except Exception:
                pass
            print(json.dumps(result))
            return 1
        finally:
            try:
                page.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass


def dump_evidence(page, args, result) -> None:
    os.makedirs(args.evidence_dir, exist_ok=True)
    tag = re.sub(r"[^a-z0-9]+", "_", (args.company or "ats").lower()).strip("_") or "ats"
    base = os.path.join(args.evidence_dir, f"ats_{tag}")
    try:
        page.screenshot(path=base + ".png", full_page=True, timeout=20000)
    except Exception:
        try:
            open(base + ".html", "w", encoding="utf-8").write(page.content())
        except Exception:
            pass
    try:
        open(base + "_text.txt", "w", encoding="utf-8").write(
            page.evaluate("() => document.body.innerText") or "")
    except Exception:
        pass
    result["evidence"] = base


if __name__ == "__main__":
    sys.exit(main())
