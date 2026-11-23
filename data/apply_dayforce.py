"""Dayforce (dayforcehcm.com) apply driver — Playwright over the user's visible Chrome (CDP 9334).

Flow: job URL -> Apply -> 'Apply without an Account' -> manualApplication form
  Step 1 (Candidate Info): resume upload, personal info, US address, most recent job, most recent degree
  Step 2 (Questionnaire): rule-based answers (EEO->No, work auth->Yes, sponsorship->Yes, relocation->No,
                          clearance question -> REJECT without submitting)
  Submit (flags reCAPTCHA if present).

Usage: python data/apply_dayforce.py --url <job-or-apply-url> --resume <pdf> [--dry-run]
JSON result on the last line.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

import playwright.sync_api as pw

CDP = "http://127.0.0.1:9334"

A = {
    "first_name": "Manish", "last_name": "Badugu",
    "email": "badugu.m7@gmail.com", "phone": "9408436058",
    "linkedin": "https://www.linkedin.com/in/badugu-manish-2241/",
    "street": "Almond Willow CV", "city": "Collierville", "state": "Tennessee", "zip": "38017",
    "country": "United States",
    # most recent job (master resume)
    "job_title": "Sr. Java Full Stack Developer", "job_company": "Verizon Communications",
    "job_start": "2025-07-01",
    # most recent degree
    "degree": "Master of Science", "major": "Computer and Information Systems",
    "school": "Christian Brothers University", "edu_start": "2023-01-01", "edu_end": "2024-05-01",
}

def log(*a):
    print(*a, flush=True)

def ant_select(page, sel, text, timeout=6000, tries=2):
    """Ant-design search combobox: click, type, pick the option containing text. `sel` is a selector string or a locator."""
    loc = sel if hasattr(sel, "click") else page.locator(sel)
    for attempt in range(tries):
        try:
            loc.first.click(timeout=4000)
        except Exception:
            return False
        time.sleep(0.6)
        # options may load async — wait for the list
        try:
            page.wait_for_selector(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option", timeout=5000)
        except Exception:
            pass
        try:
            loc.first.fill(text, timeout=4000)
        except Exception:
            pass
        time.sleep(1.5)
        opt = page.locator(f".ant-select-dropdown:visible .ant-select-item-option:has-text('{text}')").first
        try:
            opt.click(timeout=timeout)
            time.sleep(0.6)
            return True
        except Exception:
            pass
        try:
            page.locator(".ant-select-dropdown:visible .ant-select-item-option").first.click(timeout=3000)
            time.sleep(0.6)
            return True
        except Exception:
            page.keyboard.press("Escape")
            time.sleep(0.5)
    return False

def fill_text(page, sel, value):
    for attempt in range(2):
        try:
            el = page.locator(sel).first
            el.scroll_into_view_if_needed(timeout=4000)
            el.fill(value, timeout=6000)
            return True
        except Exception:
            time.sleep(1)
    return False

def recaptcha_challenge_visible(page):
    """True only if an interactive reCAPTCHA challenge is actually shown (not the invisible widget)."""
    try:
        if page.locator("text=I'm not a robot").first.is_visible(timeout=800):
            return True
    except Exception:
        pass
    try:
        for i in range(page.locator("iframe[src*='recaptcha']").count()):
            f = page.locator("iframe[src*='recaptcha']").nth(i)
            src = f.get_attribute("src") or ""
            if "bframe" not in src:
                continue  # invisible anchor widget
            box = f.bounding_box()
            if box and box["width"] > 300 and box["height"] > 200:
                return True
    except Exception:
        pass
    return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--resume", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    result = {"status": "needs_manual", "filled": [], "empty": [], "error": None, "questions": [], "evidence": None}
    browser = None
    try:
        browser = pw.sync_playwright().start().chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        page = ctx.new_page()
        page.goto(args.url, timeout=45000)
        page.wait_for_load_state("domcontentloaded", timeout=30000)
        time.sleep(2.5)

        # cookie banner
        for label in ("Accept", "Accept All", "Got it"):
            try:
                b = page.locator(f"button:has-text('{label}')").first
                if b.is_visible(timeout=1200):
                    b.click()
                    time.sleep(0.6)
            except Exception:
                pass

        # if on a job page, start the apply flow
        if "/apply/" not in page.url:
            try:
                page.wait_for_load_state("networkidle", timeout=25000)
            except Exception:
                pass
            time.sleep(2)
            clicked = False
            for sel in ("button.ant-btn-primary:has-text('Apply')", "button:has-text('Apply')", "a:has-text('Apply')"):
                try:
                    b = page.locator(sel).first
                    b.wait_for(state="visible", timeout=4000)
                    b.click()
                    clicked = True
                    break
                except Exception:
                    pass
            if not clicked:
                result["error"] = "no Apply button"
                dump(page, result, args)
                return 0
            try:
                page.wait_for_url("**/apply**", timeout=30000)
            except Exception:
                result["error"] = f"clicked Apply but URL stayed {page.url}"
                dump(page, result, args)
                return 0
            time.sleep(3)
        if "flowSelection" in page.url:
            clicked = False
            for sel in ("button:has-text('Apply without an Account')", "a:has-text('Apply without an Account')"):
                try:
                    b = page.locator(sel).first
                    b.wait_for(state="visible", timeout=15000)
                    b.click()
                    clicked = True
                    break
                except Exception:
                    pass
            if clicked:
                try:
                    page.wait_for_url("**/manualApplication**", timeout=30000)
                except Exception:
                    pass
                time.sleep(3)
        if "manualApplication" not in page.url:
            result["error"] = f"not on manual application form: {page.url}"
            dump(page, result, args)
            return 0

        # ---- Step 1: Candidate Info ----
        page.wait_for_selector("input#jobPostingApplication_files_resume", timeout=30000, state="attached")
        time.sleep(2)

        # resume upload first (ATS autofill may fill the rest) — duplicate ids in DOM, take first
        file_in = page.locator("input#jobPostingApplication_files_resume").first
        file_in.set_input_files(str(Path(args.resume).resolve()))
        result["filled"].append("resume")
        # Dayforce parses the resume and imports work history + education — wait for it
        time.sleep(10)

        pairs = [
            ("#jobPostingApplication_personalInfo_email", A["email"]),
            ("#jobPostingApplication_personalInfo_confirmEmail", A["email"]),
            ("#jobPostingApplication_personalInfo_firstName", A["first_name"]),
            ("#jobPostingApplication_personalInfo_lastName", A["last_name"]),
            ("#jobPostingApplication_personalInfo_linkedInURL", A["linkedin"]),
            ("#jobPostingApplication_personalInfo_homePhone", A["phone"]),
            ("#jobPostingApplication_personalInfo_mobilePhone", A["phone"]),
            ("#jobPostingApplication_personalInfo_address1", A["street"]),
            ("#jobPostingApplication_personalInfo_city", A["city"]),
            ("#jobPostingApplication_personalInfo_postalCode", A["zip"]),
        ]
        for sel, val in pairs:
            if fill_text(page, sel, val):
                result["filled"].append(sel.lstrip("#").split("_")[-1])
            else:
                result["empty"].append(sel.lstrip("#"))
            time.sleep(0.35)

        # ---- Work history + education: use resume-imported rows when present ----
        page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
        time.sleep(1.5)
        imported = page.evaluate("""() => {
          const txt = document.body.innerText || '';
          return {
            work: [...document.querySelectorAll('input[id*="workHistory_"]')].filter(e => (e.value || '').trim()).map(e => e.value).slice(0, 8),
            edu: [...document.querySelectorAll('input[id*="educationHistory_"]')].filter(e => (e.value || '').trim()).map(e => e.value).slice(0, 8),
            hasVerizon: /verizon/i.test(txt),
            hasMS: /master of science/i.test(txt)
          };
        }""")
        if imported["work"]:
            result["filled"].append(f"work_history_imported({len(imported['work'])} fields)")
        else:
            for sel, val in [
                ("#jobPostingApplication_workHistory_0_title", A["job_title"]),
                ("#jobPostingApplication_workHistory_0_companyName", A["job_company"]),
                ("#jobPostingApplication_workHistory_0_effectiveStart", A["job_start"]),
            ]:
                if fill_text(page, sel, val):
                    result["filled"].append(sel.lstrip("#").split("_")[-1])
                else:
                    result["empty"].append(sel.lstrip("#"))
            try:
                page.locator("#jobPostingApplication_workHistory_0_isCurrent").first.check(timeout=3000)
                result["filled"].append("isCurrent")
            except Exception:
                pass
        if imported["edu"]:
            result["filled"].append(f"education_imported({len(imported['edu'])} fields)")
        else:
            for sel, val in [
                ("#jobPostingApplication_educationHistory_0_degreeName", A["degree"]),
                ("#jobPostingApplication_educationHistory_0_majorName", A["major"]),
                ("#jobPostingApplication_educationHistory_0_schoolName", A["school"]),
                ("#jobPostingApplication_educationHistory_0_effectiveStart", A["edu_start"]),
                ("#jobPostingApplication_educationHistory_0_effectiveEnd", A["edu_end"]),
            ]:
                if fill_text(page, sel, val):
                    result["filled"].append(sel.lstrip("#").split("_")[-1])
                else:
                    result["empty"].append(sel.lstrip("#"))
        # ant-selects: phone dialing codes (by aria-label, ids are generated), preferred contact, state/country
        dial = page.locator('input[aria-label="Country dialing code"]')
        for i in range(min(dial.count(), 2)):
            if ant_select(page, dial.nth(i), A["country"]):
                result["filled"].append(f"dialcode_{i}")
            else:
                result["empty"].append(f"dialcode_{i}")
        if ant_select(page, "#jobPostingApplication_personalInfo_countryCode", A["country"]):
            result["filled"].append("countryCode")
        else:
            result["empty"].append("countryCode")
        if ant_select(page, "#jobPostingApplication_personalInfo_stateCode", A["state"]):
            result["filled"].append("stateCode")
        elif ant_select(page, "#jobPostingApplication_personalInfo_stateCode", "TN"):
            result["filled"].append("stateCode")
        else:
            result["empty"].append("stateCode")
        if ant_select(page, "#jobPostingApplication_personalInfo_preferredContactMethod", "Email"):
            result["filled"].append("preferredContactMethod")
        else:
            result["empty"].append("preferredContactMethod")

        # ---- Step 2: Questionnaire ----
        nxt = page.locator("button:has-text('Next')").first
        nxt.scroll_into_view_if_needed()
        nxt.click()
        time.sleep(4)

        # answer every visible radio group by label rules
        groups = page.locator(".ant-form-item, .ant-row:has(input[type=radio])")
        n_groups = groups.count()
        seen = set()
        for i in range(min(n_groups, 40)):
            g = groups.nth(i)
            try:
                gtext = (g.inner_text(timeout=1000) or "").strip()
            except Exception:
                continue
            key = re.sub(r"\s+", " ", gtext)[:90]
            if not key or key in seen:
                continue
            radios = g.locator("input[type=radio]")
            if radios.count() == 0:
                continue
            seen.add(key)
            low = key.lower()
            choice = None
            if re.search(r"(security clearance|cleared|it ar)", low):
                dump(page, result, args)
                result["status"] = "rejected_clearance"
                result["error"] = "form asks about security clearance"
                return 0
            if re.search(r"(diversity|under.?represent|veteran|hispanic|race|ethnic|disability|disabled|lgbt|neuro|caregiv|accommodat|protected)", low):
                choice = "No"
            elif re.search(r"(authorized to work|legally authorized)", low):
                choice = "Yes"
            elif re.search(r"(visa sponsorship|sponsor you|sponsorship)", low):
                choice = "Yes"
            elif re.search(r"(relocat|will you move|willing to move)", low):
                choice = "No"
            elif re.search(r"(currently employed|are you currently employed)", low):
                choice = "Yes"
            elif re.search(r"(right to work)", low):
                choice = "Yes"
            if choice:
                try:
                    lab = g.locator(f"label:has-text('{choice}')").first
                    lab.locator("input[type=radio]").check(timeout=2500)
                    result["questions"].append({"q": key[:120], "a": choice})
                except Exception:
                    try:
                        for r in g.locator("input[type=radio]").all():
                            lbl = r.evaluate("el => el.closest('label') ? el.closest('label').innerText : ''")
                            if lbl.strip().lower() == choice.lower():
                                r.check(timeout=2000)
                                result["questions"].append({"q": key[:120], "a": choice})
                                break
                    except Exception:
                        result["questions"].append({"q": key[:120], "a": "SKIPPED"})
            else:
                result["questions"].append({"q": key[:120], "a": "LEAVE_BLANK"})

        # ---- Submit (invisible reCAPTCHA runs in background; only a real challenge blocks) ----
        if args.dry_run:
            result["status"] = "dry_run_stopped"
            dump(page, result, args)
            return 0
        sub = None
        for label in ("Submit Application", "Submit", "Finish", "Complete"):
            try:
                b = page.locator(f"button:has-text('{label}')").first
                if b.is_visible(timeout=1500):
                    sub = b
                    break
            except Exception:
                pass
        if sub is None:
            result["error"] = "no submit button found"
            dump(page, result, args)
            return 0
        sub.scroll_into_view_if_needed()
        sub.click()
        time.sleep(6)
        # reCAPTCHA challenge can appear on submit
        if recaptcha_challenge_visible(page):
            result["status"] = "blocked_recaptcha"
            result["error"] = "reCAPTCHA challenge appeared on submit — user must clear manually (form data preserved)"
            dump(page, result, args)
            return 0
        body = (page.inner_text("body", timeout=10000) or "")
        if re.search(r"(thank|application (has been )?(submitted|received)|successfully|confirmation|we'll be in touch|next steps)", body, re.I):
            result["status"] = "submitted"
        else:
            result["status"] = "submitted_unverified"
            result["error"] = "clicked submit; no confirmation marker"
        dump(page, result, args)
        return 0
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        try:
            dump(page, result, args)
        except Exception:
            pass
        return 1
    finally:
        try:
            if browser:
                browser.close()
        except Exception:
            pass

def dump(page, result, args):
    ev = Path("data/evidence") / ("dayforce_" + re.sub(r"[^a-z0-9]+", "_", args.url.split("/")[2])[-40:])
    ev.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(ev.with_suffix(".png")), full_page=True)
        result["evidence"] = str(ev.with_suffix(".png"))
    except Exception:
        pass
    try:
        (ev.with_suffix(".txt")).write_text(page.inner_text("body", timeout=10000) or "", encoding="utf-8")
    except Exception:
        pass
    print(json.dumps(result))

if __name__ == "__main__":
    sys.exit(main())
