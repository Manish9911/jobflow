"""Unit tests for the JD eligibility gate (agent's read-the-JD-first step)."""
from backend.app.services.eligibility import assess_jd


def test_us_citizens_only_rejects():
    r = assess_jd("We are seeking an engineer. US citizens only.")
    assert r["decision"] == "reject"
    assert any("us_citizens_only" in x for x in r["reasons"])


def test_must_be_us_citizen_rejects():
    r = assess_jd("The selected candidate must be a US citizen at time of hire.")
    assert r["decision"] == "reject"


def test_us_persons_only_rejects():
    r = assess_jd("This role is restricted to US persons only.")
    assert r["decision"] == "reject"


def test_no_sponsorship_rejects():
    r = assess_jd("We are not able to sponsor candidates for work visas.")
    assert r["decision"] == "reject"
    assert any("no_sponsorship" in x for x in r["reasons"])


def test_will_not_sponsor_rejects():
    r = assess_jd("Note: the company will not sponsor for H1B.")
    assert r["decision"] == "reject"


def test_no_visa_sponsorship_rejects():
    r = assess_jd("No visa sponsorship available for this position.")
    assert r["decision"] == "reject"


def test_future_sponsorship_boilerplate_rejects():
    jd = ("You must be authorized to work in the United States and not require, "
          "now or in the future, sponsorship for work authorization.")
    r = assess_jd(jd)
    assert r["decision"] == "reject"


def test_sponsorship_offered_applies():
    r = assess_jd("We offer visa sponsorship for the right candidate.")
    assert r["decision"] == "apply"
    assert r["checked"] is True
    assert any("offers_sponsorship" in x for x in r["signals"])


def test_silence_applies():
    jd = "Build delightful products with React and Go. 4+ years of experience."
    r = assess_jd(jd)
    assert r["decision"] == "apply"
    assert r["checked"] is True
    assert r["reasons"] == []


def test_empty_jd_applies_unchecked():
    r = assess_jd("")
    assert r["decision"] == "apply"
    assert r["checked"] is False
    r2 = assess_jd(None)
    assert r2["decision"] == "apply"
    assert r2["checked"] is False


def test_will_sponsor_is_not_a_reject():
    # "will sponsor" must not be caught by the "will not sponsor" pattern.
    r = assess_jd("We will sponsor your H1B visa if needed.")
    assert r["decision"] == "apply"


def test_sponsorship_not_offered_rejects():
    r = assess_jd("Sponsorship is not available for this role.")
    assert r["decision"] == "reject"


def test_rejection_quotes_the_phrase():
    jd = "This is a long job description. " * 20 + "US citizens only." + " " * 40
    r = assess_jd(jd)
    assert r["decision"] == "reject"
    assert any("US citizens only" in x for x in r["reasons"])


def test_security_clearance_rejects():
    r = assess_jd("This role requires the candidate be eligible to obtain and "
                  "maintain a U.S. security clearance.")
    assert r["decision"] == "reject"
    assert any("clearance_required" in x for x in r["reasons"])


def test_active_clearance_rejects():
    r = assess_jd("Must hold an active TS/SCI clearance and pass background checks.")
    assert r["decision"] == "reject"
    assert any("clearance_required" in x for x in r["reasons"])


def test_clearance_eligibility_question_rejects():
    r = assess_jd("Clearance eligibility: Do you hold a valid security clearance?")
    assert r["decision"] == "reject"


def test_benign_clearance_word_applies():
    # "clearance" outside a security context must NOT trip the gate.
    r = assess_jd("We run inventory clearance sales in our warehouse. "
                  "Spring Boot, PostgreSQL, AWS. We sponsor H1B.")
    assert r["decision"] == "apply"


# ---------------------------------------------------------------------------
# STEM-OPT-only (user rule 2026-11-05: cheap parameter pre-screen)
# ---------------------------------------------------------------------------

def test_stem_opt_eligibility_rejects():
    r = assess_jd("You must be eligible for a STEM OPT extension to qualify.")
    assert r["decision"] == "reject"
    assert any("stem_opt_only" in x for x in r["reasons"])


def test_maintain_stem_opt_rejects():
    r = assess_jd("Candidates must maintain STEM OPT status during the contract.")
    assert r["decision"] == "reject"
    assert any("stem_opt_only" in x for x in r["reasons"])


def test_stem_opt_in_sponsorship_list_applies():
    # Listing STEM OPT among sponsored visa categories is neutral, not a
    # STEM-OPT-only requirement.
    r = assess_jd("We will sponsor H1B, L1 and STEM OPT candidates.")
    assert r["decision"] == "apply"
    assert not any("stem_opt_only" in x for x in r["reasons"])


# ---------------------------------------------------------------------------
# Experience ceiling (user rule 2026-11-05: parameter pre-screen)
# ---------------------------------------------------------------------------

def test_far_above_experience_rejects():
    r = assess_jd("We require 8+ years of experience in distributed systems.")
    assert r["decision"] == "reject"
    assert any("experience_mismatch" in x for x in r["reasons"])


def test_range_above_experience_rejects():
    r = assess_jd("This is a senior role requiring 10 to 12 years of experience.")
    assert r["decision"] == "reject"
    assert any("experience_mismatch" in x for x in r["reasons"])


def test_borderline_experience_applies():
    # 5+ is borderline against a 4+ year resume — still applies (user reviews).
    r = assess_jd("5 years of experience required. We are open to sponsorship.")
    assert r["decision"] == "apply"


def test_low_experience_applies():
    r = assess_jd("3 to 5 years of Java experience. We sponsor H1B.")
    assert r["decision"] == "apply"


def test_range_masked_uses_low_end():
    from backend.app.services.eligibility import required_experience_years
    assert required_experience_years("8 to 10 years of experience") == 8
    assert required_experience_years("5 to 8 years of experience") == 5
    assert required_experience_years("5+ years of experience") == 5
    assert required_experience_years("minimum of 7 years") == 7
    assert required_experience_years("6 or more years") == 6
    assert required_experience_years("no number here") is None


# ---------------------------------------------------------------------------
# JD stack fit (user rule 2026-11-05: judge by the JD, not the title)
# ---------------------------------------------------------------------------

RESUME_SKILLS = ["Java", "Spring Boot", "React", "PostgreSQL", "SQL",
                 "AWS", "REST APIs", "Microservices"]


def test_stack_mismatch_applies_and_reports_missing():
    # USER RULE 2026-11-18: stack mismatch NEVER rejects — apply anyway, and
    # report the JD skills the resume lacks so tailoring can ADD them.
    from backend.app.services.eligibility import assess_jd_skills
    r = assess_jd_skills(
        "We need GraphQL, MongoDB, Redis and Kafka experts for the event platform.",
        RESUME_SKILLS)
    assert r["decision"] == "apply"
    assert r["missing"], "expected the resume-lacking JD skills to be reported"
    assert not (set(r["hits"]) & set(r["missing"]))
    assert any("jd_skills_to_add" in x for x in r["reasons"])


def test_stack_fit_applies():
    from backend.app.services.eligibility import assess_jd_skills
    r = assess_jd_skills(
        "Java Spring Boot backend with React frontend, PostgreSQL on AWS, "
        "REST APIs and microservices.",
        RESUME_SKILLS)
    assert r["decision"] == "apply"


def test_partial_overlap_applies():
    # Borderline overlap (1 hit) is NOT a clear mismatch — passes for review.
    from backend.app.services.eligibility import assess_jd_skills
    r = assess_jd_skills(
        "Platform team: GraphQL, MongoDB, Redis, plus SQL for reporting.",
        RESUME_SKILLS)
    assert r["decision"] == "apply"


def test_unknown_stack_has_no_signal():
    # JD names no canonical skills at all — nothing to judge, passes.
    from backend.app.services.eligibility import assess_jd_skills
    r = assess_jd_skills("Looking for iOS developers with Swift and UIKit.",
                         RESUME_SKILLS)
    assert r["decision"] == "apply"


# --- Title-level gate (rejection lessons 2026-11-23: Elastic Principal,
#     Garmin Mobile iOS, Affirm Manager ML) ---

def test_title_principal_rejects():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Principal Java Engineer - Distributed Systems, Serverless - Elasticsearch")
    assert r["decision"] == "reject"
    assert any("seniority_mismatch" in x for x in r["reasons"])


def test_title_staff_engineer_rejects():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Staff Software Engineer, Backend")
    assert r["decision"] == "reject"
    assert any("seniority_mismatch" in x for x in r["reasons"])


def test_title_manager_rejects():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Manager, Machine Learning Engineering, Checkout")
    assert r["decision"] == "reject"
    assert any("seniority_mismatch" in x for x in r["reasons"])


def test_title_director_rejects():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Director of Engineering, Platform")
    assert r["decision"] == "reject"


def test_title_ios_rejects():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Senior Software Engineer - Mobile iOS")
    assert r["decision"] == "reject"
    assert any("mobile_discipline" in x for x in r["reasons"])


def test_title_android_rejects():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Android Developer")
    assert r["decision"] == "reject"
    assert any("mobile_discipline" in x for x in r["reasons"])


def test_title_senior_java_applies():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Senior Java Backend Developer")
    assert r["decision"] == "apply"
    assert r["reasons"] == []


def test_title_fullstack_applies():
    from backend.app.services.eligibility import assess_title
    r = assess_title("Senior Full Stack Developer, React + Spring Boot")
    assert r["decision"] == "apply"
    assert r["reasons"] == []


def test_title_none_applies():
    from backend.app.services.eligibility import assess_title
    r = assess_title(None)
    assert r["decision"] == "apply"


# --- False-positive fixes (live incidents 2026-11-23) ---

def test_years_of_age_is_not_experience():
    # Bank of America: "you must be at least 18 years of age" is a legal-age
    # statement, not a YOE requirement.
    from backend.app.services.eligibility import required_experience_years
    assert required_experience_years(
        "To proceed with your application, you must be at least 18 years of age. "
        "We seek 3+ years of Java experience.") == 3


def test_years_of_age_alone_yields_no_requirement():
    from backend.app.services.eligibility import required_experience_years
    assert required_experience_years(
        "Applicants must be at least 18 years of age. Acknowledge.") is None


def test_fee_reassurance_does_not_flag():
    # Optum/UnitedHealth: "we will never request you to pay a fee of any
    # sort" is a reassurance, not a fee demand.
    from backend.app.services.fraud import assess_job_fraud
    r = assess_job_fraud(
        "Full Stack Engineer - Java. "
        "UnitedHealth Group will never request you to pay a vendor or "
        "pay a fee of any sort to explore employment opportunities.",
        "https://jobs.optum.com/job/memphis-tn/full-stack-engineer/1234567",
        "https://www.optum.com")
    assert r["decision"] != "reject", r["reasons"]


def test_real_fee_demand_still_flags():
    from backend.app.services.fraud import assess_job_fraud
    r = assess_job_fraud(
        "To apply you must pay a fee of $50. Wire transfer to our account.",
        "https://example.com/apply", None)
    assert r["decision"] == "reject"


def test_company_brag_years_not_a_requirement():
    # Talan (live 2026-11-23): "our cross-disciplinary teams bring over 30
    # years of experience helping business leaders" describes the employer,
    # not the candidate. Must not be read as a 30-year minimum.
    from backend.app.services.eligibility import (
        required_experience_years, assess_jd)
    jd = ("Senior Java Developer. About us: our cross-disciplinary teams "
          "bring over 30 years of experience helping business leaders "
          "across key industries. You will have 4 years of experience "
          "with Java and Spring Boot.")
    assert required_experience_years(jd) == 4
    r = assess_jd(jd)
    assert r["decision"] == "apply", r["reasons"]


def test_company_brag_with_over_years_masked():
    from backend.app.services.eligibility import required_experience_years
    jd = ("With over 25 years of experience in IT services, we deliver. "
          "Candidates need 5+ years of backend experience.")
    # 25 (employer history) masked; 5+ (real minimum) is what remains.
    assert required_experience_years(jd) == 5


def test_plain_with_years_requirement_still_counts():
    # "someone with 8 years of experience" is a real requirement — the
    # brag mask must not eat it (only "with OVER/more than N years" is
    # employer-history phrasing).
    from backend.app.services.eligibility import required_experience_years
    jd = ("We are looking for someone with 8 years of experience in "
          "distributed systems.")
    assert required_experience_years(jd) == 8


def test_experience_quote_points_at_real_phrase():
    # Fanatics (live 2026-11-23): the quote must come from the actual
    # "N years" requirement, not the first unrelated occurrence of the
    # digit (the JD's "over 7,000 athletes" was being quoted for a 7-yr
    # minimum that lives elsewhere in the text).
    from backend.app.services.eligibility import assess_jd
    jd = ("Serving over 7,000 athletes and celebrities. "
          "The position requires 7+ years of hands-on Java experience "
          "in a high-throughput environment.")
    r = assess_jd(jd)
    assert r["decision"] == "reject"
    quoted = " ".join(r["reasons"])
    assert "7+ years of hands-on" in quoted, quoted
    assert "7,000 athletes" not in quoted, quoted
