"""One-shot direct ATS board fetcher (Greenhouse / Lever / Ashby / SmartRecruiters).

Pulls public job-board JSON straight from each ATS (no aggregator), normalizes
into jobflow's job dict shape, runs the standard filters + matching via
store_jobs(), and prints the new high-score jobs.

Usage:  .venv/Scripts/python.exe data/fetch_direct_boards.py
"""
from __future__ import annotations

import html as html_mod
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402

from backend.app.db.base import make_engine, make_session  # noqa: E402
from backend.app.ingestion.service import store_jobs  # noqa: E402

DB_PATH = ROOT / "data" / "jobflow.db"
CACHE_PATH = ROOT / "data" / "direct_boards_cache.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# (slug, company_name, hq_country) — hq_country is the fallback for
# remote/unknown locations so the US/EU filter can place the role.
GREENHOUSE = [
    ("intuit", "Intuit", "US"),
    ("fiserv", "Fiserv", "US"),
    ("factset", "FactSet", "US"),
    ("synchrony", "Synchrony", "US"),
    ("chime", "Chime", "US"),
    ("robinhood", "Robinhood", "US"),
    ("block", "Block", "US"),
    ("adyen", "Adyen", "NL"),
    ("klarna", "Klarna", "SE"),
    ("revolut", "Revolut", "GB"),
    ("n26", "N26", "DE"),
    ("traderepublic", "Trade Republic", "DE"),
    ("bunq", "bunq", "NL"),
    ("starlingbank", "Starling Bank", "GB"),
    ("monzo", "Monzo", "GB"),
    ("wise", "Wise", "GB"),
    ("docusign", "DocuSign", "US"),
    ("box", "Box", "US"),
    ("mulesoft", "MuleSoft", "US"),
    ("twilio", "Twilio", "US"),
    ("datadog", "Datadog", "US"),
    ("cloudflare", "Cloudflare", "US"),
    ("okta", "Okta", "US"),
    ("gitlab", "GitLab", "US"),
    ("atlassian", "Atlassian", "US"),
    ("shopify", "Shopify", "US"),
    ("bookingcom", "Booking Holdings", "US"),
    ("miro", "Miro", "DE"),
    ("snowflake", "Snowflake", "US"),
    ("elastic", "Elastic", "US"),
    ("mongodb", "MongoDB", "US"),
    ("databricks", "Databricks", "US"),
    ("hashicorp", "HashiCorp", "US"),
    ("ansys", "Ansys", "US"),
    ("schneider", "Schneider Electric", "FR"),
    ("qualcomm", "Qualcomm", "US"),
    ("hpe", "Hewlett Packard Enterprise", "US"),
    ("plaid", "Plaid", "US"),
    ("ramp", "Ramp", "US"),
    ("brex", "Brex", "US"),
    ("affirm", "Affirm", "US"),
    ("sofi", "SoFi", "US"),
    ("lendingtree", "LendingTree", "US"),
    ("navient", "Navient", "US"),
    ("zendesk", "Zendesk", "US"),
    ("asana", "Asana", "US"),
    ("figma", "Figma", "US"),
    ("canva", "Canva", "AU"),
    ("airtable", "Airtable", "US"),
    ("notion", "Notion", "US"),
    ("intercom", "Intercom", "US"),
    ("monday", "Monday.com", "US"),
    ("smartsheet", "Smartsheet", "US"),
    ("veeva", "Veeva Systems", "US"),
    ("jasper", "Jasper", "US"),
    ("elevenlabs", "ElevenLabs", "US"),
    ("perplexity", "Perplexity AI", "US"),
    ("cursor", "Cursor", "US"),
    ("midjourney", "Midjourney", "US"),
    ("runway", "Runway", "US"),
    ("loom", "Loom", "US"),
    ("sentry", "Sentry", "US"),
    ("launchdarkly", "LaunchDarkly", "US"),
    ("supabase", "Supabase", "US"),
    ("vercel", "Vercel", "US"),
    ("framer", "Framer", "SE"),
    ("clickhouse", "ClickHouse", "US"),
    ("temporal", "Temporal", "US"),
    ("prisma", "Prisma", "DE"),
    ("upstash", "Upstash", "US"),
    ("neon", "Neon", "US"),
    ("digitalocean", "DigitalOcean", "US"),
    ("vultr", "Vultr", "US"),
    ("kinsta", "Kinsta", "US"),
    ("fly", "Fly.io", "US"),
    ("render", "Render", "US"),
    ("cal", "Cal.com", "US"),
    ("nylas", "Nylas", "US"),
    ("posthog", "PostHog", "US"),
    ("trpc", "tRPC", "US"),
    ("resend", "Resend", "US"),
    ("supertokens", "SuperTokens", "IN"),
    ("vanta", "Vanta", "US"),
    ("retool", "Retool", "US"),
    ("linear", "Linear", "US"),
    ("drata", "Drata", "US"),
    ("abridge", "Abridge", "US"),
    ("harvey", "Harvey", "US"),
    ("anthropic", "Anthropic", "US"),
    ("stripe", "Stripe", "US"),
    ("coinbase", "Coinbase", "US"),
    ("kraken", "Kraken", "US"),
    ("chainalysis", "Chainalysis", "US"),
]

LEVER = [
    ("snowflake", "Snowflake", "US"),
    ("elastic", "Elastic", "US"),
    ("asana", "Asana", "US"),
    ("zendesk", "Zendesk", "US"),
    ("airtable", "Airtable", "US"),
    ("datadog", "Datadog", "US"),
    ("figma", "Figma", "US"),
    ("canva", "Canva", "AU"),
    ("notion", "Notion", "US"),
    ("retool", "Retool", "US"),
    ("intercom", "Intercom", "US"),
    ("monday", "Monday.com", "US"),
    ("smartsheet", "Smartsheet", "US"),
    ("veeva", "Veeva Systems", "US"),
    ("jasper", "Jasper", "US"),
    ("elevenlabs", "ElevenLabs", "US"),
    ("perplexity", "Perplexity AI", "US"),
    ("cursor", "Cursor", "US"),
    ("midjourney", "Midjourney", "US"),
    ("runway", "Runway", "US"),
    ("loom", "Loom", "US"),
    ("stripe", "Stripe", "US"),
    ("coinbase", "Coinbase", "US"),
    ("plaid", "Plaid", "US"),
    ("twilio", "Twilio", "US"),
    ("mongodb", "MongoDB", "US"),
    ("databricks", "Databricks", "US"),
    ("atlassian", "Atlassian", "US"),
    ("shopify", "Shopify", "US"),
    ("gitlab", "GitLab", "US"),
    ("okta", "Okta", "US"),
    ("mulesoft", "MuleSoft", "US"),
    ("box", "Box", "US"),
    ("docusign", "DocuSign", "US"),
    ("cloudflare", "Cloudflare", "US"),
    ("hashicorp", "HashiCorp", "US"),
    ("sentry", "Sentry", "US"),
    ("launchdarkly", "LaunchDarkly", "US"),
    ("supabase", "Supabase", "US"),
    ("vercel", "Vercel", "US"),
    ("framer", "Framer", "SE"),
    ("clickhouse", "ClickHouse", "US"),
    ("temporal", "Temporal", "US"),
    ("prisma", "Prisma", "DE"),
    ("upstash", "Upstash", "US"),
    ("neon", "Neon", "US"),
    ("digitalocean", "DigitalOcean", "US"),
    ("vultr", "Vultr", "US"),
    ("kinsta", "Kinsta", "US"),
    ("fly", "Fly.io", "US"),
    ("render", "Render", "US"),
    ("cal", "Cal.com", "US"),
    ("nylas", "Nylas", "US"),
    ("posthog", "PostHog", "US"),
    ("trpc", "tRPC", "US"),
    ("resend", "Resend", "US"),
    ("vanta", "Vanta", "US"),
    ("linear", "Linear", "US"),
    ("drata", "Drata", "US"),
    ("abridge", "Abridge", "US"),
    ("harvey", "Harvey", "US"),
    ("anthropic", "Anthropic", "US"),
    ("kraken", "Kraken", "US"),
    ("chainalysis", "Chainalysis", "US"),
]

ASHBY = [
    ("coinbase", "Coinbase", "US"),
    ("linear", "Linear", "US"),
    ("vanta", "Vanta", "US"),
    ("retool", "Retool", "US"),
    ("nylas", "Nylas", "US"),
    ("cal", "Cal.com", "US"),
    ("supertokens", "SuperTokens", "IN"),
    ("posthog", "PostHog", "US"),
    ("trpc", "tRPC", "US"),
    ("resend", "Resend", "US"),
    ("upstash", "Upstash", "US"),
    ("neon", "Neon", "US"),
    ("clickhouse", "ClickHouse", "US"),
    ("temporal", "Temporal", "US"),
    ("prisma", "Prisma", "DE"),
    ("vercel", "Vercel", "US"),
    ("framer", "Framer", "SE"),
    ("supabase", "Supabase", "US"),
    ("fly", "Fly.io", "US"),
    ("render", "Render", "US"),
    ("digitalocean", "DigitalOcean", "US"),
    ("vultr", "Vultr", "US"),
    ("kinsta", "Kinsta", "US"),
    ("sentry", "Sentry", "US"),
    ("launchdarkly", "LaunchDarkly", "US"),
    ("stripe", "Stripe", "US"),
    ("kraken", "Kraken", "US"),
    ("chainalysis", "Chainalysis", "US"),
    ("abridge", "Abridge", "US"),
    ("harvey", "Harvey", "US"),
    ("cursor", "Cursor", "US"),
    ("anthropic", "Anthropic", "US"),
    ("midjourney", "Midjourney", "US"),
    ("elevenlabs", "ElevenLabs", "US"),
    ("jasper", "Jasper", "US"),
]

SMARTRECRUITERS = [
    ("monzo", "Monzo", "GB"),
    ("bunq", "bunq", "NL"),
    ("wise", "Wise", "GB"),
    ("n26", "N26", "DE"),
    ("revolut", "Revolut", "GB"),
    ("starlingbank", "Starling Bank", "GB"),
    ("traderepublic", "Trade Republic", "DE"),
    ("adyen", "Adyen", "NL"),
    ("klarna", "Klarna", "SE"),
    ("prisma", "Prisma", "DE"),
    ("miro", "Miro", "DE"),
    ("framer", "Framer", "SE"),
]

EU_CITIES = {
    "netherlands": "NL", "amsterdam": "NL", "rotterdam": "NL", "the hague": "NL",
    "germany": "DE", "berlin": "DE", "munich": "DE", "frankfurt": "DE", "hamburg": "DE",
    "france": "FR", "paris": "FR", "lyon": "FR", "ireland": "IE", "dublin": "IE",
    "sweden": "SE", "stockholm": "SE", "spain": "ES", "madrid": "ES", "barcelona": "ES",
    "portugal": "PT", "lisbon": "PT", "porto": "PT", "denmark": "DK", "copenhagen": "DK",
    "finland": "FI", "helsinki": "FI", "austria": "AT", "vienna": "AT", "switzerland": "CH",
    "zurich": "CH", "geneva": "CH", "poland": "PL", "warsaw": "PL", "krakow": "PL",
    "czech": "CZ", "prague": "CZ", "hungary": "HU", "budapest": "HU", "belgium": "BE",
    "brussels": "BE", "netherlands": "NL", "luxembourg": "LU", "norway": "NO", "oslo": "NO",
    "romania": "RO", "bucharest": "RO", "slovakia": "SK", "bratislava": "SK", "slovenia": "SI",
    "lithuania": "LT", "vilnius": "LT", "latvia": "LV", "riga": "LV", "estonia": "EE",
    "italy": "IT", "milan": "IT", "rome": "IT", "greece": "GR", "thessaloniki": "GR",
    "croatia": "HR", "zagreb": "HR", "bulgaria": "BG", "sofia": "BG", "uk": "GB",
    "england": "GB", "scotland": "GB", "wales": "GB", "london": "GB",
}

US_HINT = re.compile(
    r"\b(usa|united states|remote -?us|remote\(us\)|remote,? us|austin|new york|san francisco"
    r"|seattle|chicago|boston|denver|los angeles|mountain view|sunnyvale|santa clara|san jose"
    r"|portland|bellevue|redmond|cambridge|washington|texas|california|florida|new jersey"
    r"|massachusetts|maryland|virginia|north carolina|georgia|ohio|michigan|illinois"
    r"|pennsylvania|oregon|utah|colorado|nevada|arizona|tampa|raleigh|rtp)\b", re.I)

NO_SPONSOR_RE = re.compile(
    r"(not able to (sponsor|provide sponsorship)|will not (sponsor|provide sponsorship)"
    r"|unable to (sponsor|provide (visa )?sponsorship)|no (visa )?sponsorship"
    r"|not (offering|provide) (visa )?sponsorship|does not (sponsor|offer sponsorship)"
    r"|we do not (sponsor|offer sponsorship)|can only hire candidates who do not require sponsorship)", re.I)
SPONSOR_RE = re.compile(
    r"(we (will |do )?sponsor|happy to sponsor|visa sponsorship (is )?(available|provided|offered)"
    r"|we offer (h1[- ]b|l1|o1|visa) (sponsorship|support)|sponsorship available for the right candidate"
    r"|eligible to work in the (us|usa) without (current or future|now or in the future) sponsorship"
    r"|do not require sponsorship)", re.I)


def strip_tags(h: str) -> str:
    t = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", h or "")
    t = re.sub(r"<[^>]+>", " ", t)
    return html_mod.unescape(re.sub(r"\s+", " ", t)).strip()


NON_TARGET_HINT = re.compile(
    r"\b(india|indian|bangalore|bengaluru|pune|mumbai|canada|vancouver|toronto|montreal"
    r"|australia|sydney|melside|melbourne|israel|tel aviv|singapore|brazil|sao paulo|são paulo"
    r"|uae|dubai|china|beijing|shanghai|shenzhen|japan|tokyo|korea|seoul|incheon"
    r"|mexico|city of mexico|new zealand|auckland|philippines|manila|thailand|bangkok"
    r"|indonesia|jakarta|vietnam|hanoi|ho chi minh|malaysia|kuala lumpur)\b", re.I)
NON_TARGET_COUNTRIES = {
    "india": "IN", "bangalore": "IN", "bengaluru": "IN", "pune": "IN", "mumbai": "IN",
    "canada": "CA", "vancouver": "CA", "toronto": "CA", "montreal": "CA",
    "australia": "AU", "sydney": "AU", "melbourne": "AU", "israel": "IL", "tel aviv": "IL",
    "singapore": "SG", "brazil": "BR", "sao paulo": "BR", "são paulo": "BR",
    "uae": "AE", "dubai": "AE", "china": "CN", "beijing": "CN", "shanghai": "CN",
    "shenzhen": "CN", "japan": "JP", "tokyo": "JP", "korea": "KR", "seoul": "KR",
    "mexico": "MX", "city of mexico": "MX", "new zealand": "NZ", "auckland": "NZ",
}


def countries_for(location: str, hq: str) -> list[str]:
    loc = (location or "").lower()
    if US_HINT.search(loc):
        return ["US"]
    for city, cc in EU_CITIES.items():
        if city in loc:
            return [cc]
    for city, cc in NON_TARGET_COUNTRIES.items():
        if city in loc:
            return [cc]
    if NON_TARGET_HINT.search(loc):
        return ["XX"]  # clearly outside US/EU — filter will drop it
    if re.search(r"\bremote\b", loc):
        return [hq]
    return [hq] if hq else []


def remote_flag(location: str) -> bool | None:
    loc = (location or "").lower()
    if "remote" in loc:
        return True
    if re.search(r"\b(us|united states|usa)\b", loc):
        return None  # US onsite — allowed
    return None


def sponsorship_flag(jd_text: str) -> bool | None:
    if NO_SPONSOR_RE.search(jd_text or ""):
        return False
    if SPONSOR_RE.search(jd_text or ""):
        return True
    return None


def parse_salary(text: str) -> tuple[int | None, int | None]:
    m = re.search(r"\$(\d{1,3}(?:,\d{3})+)(?:\s*[-–—to]+\s*\$?(\d{1,3}(?:,\d{3})+))?", text or "")
    if not m:
        return None, None
    lo = int(m.group(1).replace(",", ""))
    hi = int(m.group(2).replace(",", "")) if m.group(2) else None
    return lo, hi


def base_job(title, company, website, location, url, source, hq, jd_text="", indexed=None):
    countries = countries_for(location, hq)
    sal_lo, sal_hi = parse_salary(jd_text)
    return {
        "title": title,
        "company": company,
        "company_website": website,
        "location": location,
        "countries": countries,
        "remote": remote_flag(location),
        "visa_sponsorship": sponsorship_flag(jd_text),
        "commitment": [],
        "yoe": None,
        "salary_min": sal_lo,
        "salary_max": sal_hi,
        "salary_currency": "USD",
        "apply_url": url,
        "source": source,
        "hiringcafe_id": "",
        "indexed_at": indexed,
        "_jd_len": len(jd_text or ""),
    }


def fetch_greenhouse(client, slugs):
    out = []
    for slug, name, hq in slugs:
        try:
            r = client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
                           params={"content": 1}, timeout=15)
            if r.status_code != 200:
                print(f"  greenhouse/{slug}: {r.status_code}")
                continue
            data = r.json()
            n = 0
            for j in data.get("jobs", []):
                jd = ""
                for c in j.get("content", []) or []:
                    jd += strip_tags(c.get("content", "")) + " "
                out.append(base_job(
                    j.get("title"), data.get("board", {}).get("name", name),
                    data.get("board", {}).get("absolute_url", ""),
                    (j.get("location") or {}).get("name", ""),
                    j.get("absolute_url", ""), "greenhouse_direct", hq, jd,
                    j.get("first_published")))
                n += 1
            print(f"  greenhouse/{slug}: {n} jobs")
        except Exception as e:
            print(f"  greenhouse/{slug}: ERR {e.__class__.__name__}")
        time.sleep(0.25)
    return out


def fetch_lever(client, slugs):
    out = []
    for slug, name, hq in slugs:
        try:
            r = client.get(f"https://api.lever.co/v0/postings/{slug}",
                           params={"mode": "json"}, timeout=15)
            if r.status_code != 200:
                print(f"  lever/{slug}: {r.status_code}")
                continue
            data = r.json()
            n = 0
            for j in data if isinstance(data, list) else []:
                out.append(base_job(
                    j.get("text"), j.get("categories", {}).get("company") or name,
                    "", j.get("workLocation", ""), j.get("hostedUrl", ""),
                    "lever_direct", hq, "", j.get("createdAt")))
                n += 1
            print(f"  lever/{slug}: {n} jobs")
        except Exception as e:
            print(f"  lever/{slug}: ERR {e.__class__.__name__}")
        time.sleep(0.25)
    return out


def fetch_ashby(client, slugs):
    out = []
    for slug, name, hq in slugs:
        try:
            r = client.get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
                           params={"includeCompensation": "true"}, timeout=15)
            if r.status_code != 200:
                print(f"  ashby/{slug}: {r.status_code}")
                continue
            data = r.json()
            n = 0
            for j in data if isinstance(data, list) else []:
                loc = j.get("location") or {}
                if isinstance(loc, dict):
                    loc_s = loc.get("area", "")
                else:
                    loc_s = str(loc)
                comp = j.get("company") or {}
                website = comp.get("website") or (j.get("metadata") or {}).get("website") or ""
                sal_lo = sal_hi = None
                compen = (j.get("compensation") or [{}])[0]
                if isinstance(compen, dict):
                    t = compen.get("total") or {}
                    sal_lo = (t.get("min") or 0) or None
                    sal_hi = (t.get("max") or 0) or None
                d = base_job(j.get("title"), comp.get("name") or name, website,
                             loc_s, j.get("jobUrl", ""), "ashby_direct", hq,
                             "", j.get("publishedAt"))
                if sal_lo:
                    d["salary_min"] = sal_lo
                if sal_hi:
                    d["salary_max"] = sal_hi
                out.append(d)
                n += 1
            print(f"  ashby/{slug}: {n} jobs")
        except Exception as e:
            print(f"  ashby/{slug}: ERR {e.__class__.__name__}")
        time.sleep(0.25)
    return out


def fetch_smartrecruiters(client, slugs):
    out = []
    for slug, name, hq in slugs:
        try:
            r = client.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
                           timeout=15)
            if r.status_code != 200:
                print(f"  sr/{slug}: {r.status_code}")
                continue
            data = r.json()
            n = 0
            for p in data.get("postings", []) or []:
                locs = []
                for loc in p.get("locations", []) or []:
                    for part in (loc.get("city"), loc.get("area"), loc.get("country")):
                        if part:
                            locs.append(part)
                out.append(base_job(
                    p.get("title"), name,
                    (data.get("company") or {}).get("website", "") if "company" in data else "",
                    ", ".join(dict.fromkeys(locs)),
                    p.get("externalUrl", ""), "smartrecruiters_direct", hq, "",
                    p.get("publishDate")))
                n += 1
            print(f"  sr/{slug}: {n} jobs")
        except Exception as e:
            print(f"  sr/{slug}: ERR {e.__class__.__name__}")
        time.sleep(0.25)
    return out


def main():
    headers = {"User-Agent": UA, "Accept": "application/json"}
    jobs = []
    with httpx.Client(headers=headers, follow_redirects=True) as client:
        print("== Greenhouse ==")
        jobs += fetch_greenhouse(client, GREENHOUSE)
        print("== Lever ==")
        jobs += fetch_lever(client, LEVER)
        print("== Ashby ==")
        jobs += fetch_ashby(client, ASHBY)
        print("== SmartRecruiters ==")
        jobs += fetch_smartrecruiters(client, SMARTRECRUITERS)

    # JD text is not a Job column — cache it for the pre-screen reference.
    cache = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "jobs": [{
            "title": j["title"], "company": j["company"], "location": j["location"],
            "apply_url": j["apply_url"], "source": j["source"],
            "visa_sponsorship": j["visa_sponsorship"],
            "jd_chars": j.pop("_jd_len", 0),
        } for j in jobs],
    }
    CACHE_PATH.write_text(json.dumps(cache, indent=1), encoding="utf-8")

    engine = make_engine(f"sqlite:///{DB_PATH.as_posix()}")
    SessionLocal = make_session(engine)
    db = SessionLocal()
    try:
        result = store_jobs(db, jobs)
        print("\nSTORED:", json.dumps(result))
        from backend.app.db.models import Job
        new_jobs = (db.query(Job)
                    .filter(Job.source.in_(
                        ["greenhouse_direct", "lever_direct", "ashby_direct",
                         "smartrecruiters_direct"]))
                    .all())
        high = [j for j in new_jobs if (j.match_score or 0) >= 70
                and j.passes_filters]
        high.sort(key=lambda j: (j.match_score or 0), reverse=True)
        print(f"\nNEW HIGH-SCORE JOBS (>=70, passing filters): {len(high)}")
        for j in high[:40]:
            flag = "NOSPNR" if j.visa_sponsorship is False else ""
            print(f"  {j.match_score:3d}  {j.title[:48]:48s} | {j.company[:22]:22s} | "
                  f"{(j.location or '')[:30]:30s} | {j.source} {flag}")
        no_sponsor = [j for j in new_jobs if j.visa_sponsorship is False]
        print(f"\nJOBS WITH EXPLICIT NO-SPONSORSHIP (auto-reject): {len(no_sponsor)}")
        for j in no_sponsor[:20]:
            print(f"  {j.title[:50]:50s} | {j.company[:24]}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
