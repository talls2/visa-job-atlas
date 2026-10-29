"""Job feeds and aggregator APIs (sources that list many employers).

These cover countries with no sponsor register (Japan, Germany, Nordics) and
communities where visa terms are stated openly (HN, r/netsec). Each feed
returns job dicts like the ATS fetchers, plus:

    "company"          employer name as the feed gives it
    "default_country"  ISO-2 used when the location string names no country

Structured visa fields (Japan Dev's sponsors_visas, TokyoDev's "Apply from
abroad", Landing.jobs' relocation_paid) are turned into a short sentence
appended to the description so the normal visa-signal scoring sees them.
"""

import datetime as dt
import email.utils
import html
import json
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus

from .ats import html_to_text
from .http import FetchError, fetch, fetch_json, fetch_text
from . import scoring


def _rss_items(url):
    root = ET.fromstring(fetch(url))
    for it in root.iter():
        if it.tag.split("}")[-1] not in ("item", "entry"):
            continue
        d = {}
        for ch in it:
            tag = ch.tag.split("}")[-1]
            if tag == "link" and ch.get("href"):
                d.setdefault("link", ch.get("href"))
            elif tag not in d:
                d[tag] = (ch.text or "").strip()
        yield d


def _rss_date(s):
    if not s:
        return None
    try:
        return email.utils.parsedate_to_datetime(s).date().isoformat()
    except (TypeError, ValueError):
        return s[:10] if re.match(r"\d{4}-\d\d-\d\d", s) else None


def _job(ext_id, title, company, location, url, posted, desc, country, **extra):
    return {"ext_id": str(ext_id), "title": html.unescape(title or "").strip(), "company": (company or "").strip(),
            "location": location or "", "url": url, "posted_at": posted, "department": "", "remote": None,
            "salary": extra.get("salary"), "description": desc or "", "default_country": country}


def _relevant(title, text=""):
    return scoring.role_tier(title) or scoring.role_tier(text[:200])


# ------------------------------------------------------------------ Japan Dev
# The ?keyword= filter is applied client-side only, but these tag pages are
# server-rendered with their own result sets. Unknown tags fall back to /jobs.
JAPANDEV_PAGES = ["jobs", "backend-jobs-in-japan", "frontend-jobs-in-japan", "security-jobs-in-japan",
                  "devops-jobs-in-japan", "sre-jobs-in-japan", "data-jobs-in-japan", "mobile-jobs-in-japan"]


def japandev(pages=None):
    """Japan Dev server-renders an Algolia result set into __NUXT_DATA__; its
    records carry sponsors_visas / candidate_location / japanese_level fields."""
    out = {}
    for kw in pages or JAPANDEV_PAGES:
        page = fetch_text(f"https://japan-dev.com/{kw}")
        m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
        if not m:
            raise FetchError("Japan Dev page layout changed (no __NUXT_DATA__)")
        data = json.loads(m.group(1))
        hrefs = dict((s, c) for c, s in re.findall(r'href="/jobs/([^/"]+)/([^/"]+)"', page))

        def val(x):
            return data[x] if isinstance(x, int) and 0 <= x < len(data) else x

        for rec in data:
            if not (isinstance(rec, dict) and "sponsors_visas" in rec):
                continue
            slug = val(rec["slug"])
            if not isinstance(slug, str) or slug in out:
                continue
            sponsors = val(rec.get("sponsors_visas")) == "sponsors_visas_yes"
            anywhere = val(rec.get("candidate_location")) == "candidate_location_anywhere"
            jp = str(val(rec.get("japanese_level_enum")) or "").replace("japanese_level_", "")
            facts = []
            if sponsors:
                facts.append("Visa sponsorship available (Japan Dev field).")
            if anywhere:
                facts.append("Apply from abroad: candidates accepted from anywhere.")
            facts.append(f"Japanese level: {jp or 'unknown'}.")
            body = " ".join(html_to_text(str(val(rec.get(k)) or "")) for k in ("intro", "details", "requirements"))
            smin, smax = val(rec.get("salary_min")), val(rec.get("salary_max"))
            company_slug = hrefs.get(slug, "")
            out[slug] = _job(
                val(rec.get("id")), val(rec.get("title")), val(rec.get("company_name")),
                f"{val(rec.get('location')) or 'Japan'} (JP)",
                f"https://japan-dev.com/jobs/{company_slug}/{slug}" if company_slug else f"https://japan-dev.com/{kw}",
                str(val(rec.get("published_at")) or "")[:10] or None,
                " ".join(facts) + "\n" + body, "JP",
                salary=f"¥{smin:,}-¥{smax:,}" if isinstance(smin, int) and isinstance(smax, int) else None,
            )
    return list(out.values())


# ------------------------------------------------------------------- TokyoDev
def tokyodev():
    page = fetch_text("https://www.tokyodev.com/jobs")
    out = []
    for block in re.split(r'<li id="company_', page)[1:]:
        m = re.search(r'<h3[^>]*>\s*<a[^>]*>(.*?)</a>', block, re.S)
        company = html.unescape(m.group(1)).strip() if m else ""
        for href, title, tags in re.findall(
                r'href="(/companies/[^"]+/jobs/[^"]+)">(.*?)</a>\s*</div>\s*<div class="flex gap-2[^"]*">(.*?)</div>', block, re.S):
            tag_list = [html.unescape(t).strip() for t in re.findall(r'<a[^>]*class="[^"]*tag[^"]*"[^>]*>(.*?)</a>', tags, re.S)]
            facts = []
            if "Apply from abroad" in tag_list:
                facts.append("Apply from abroad (TokyoDev: company supports visa for overseas hires).")
            facts.append("Tags: " + ", ".join(tag_list))
            salary = next((t for t in tag_list if t.startswith("¥")), None)
            out.append(_job(href.rsplit("/", 1)[-1] + "@" + href.split("/")[2], title, company, "Tokyo (JP)",
                            "https://www.tokyodev.com" + href, None, " ".join(facts), "JP", salary=salary))
    return out


# --------------------------------------------------------- Hacker News hiring
def _hn_comment_job(c, story_title):
    text = html_to_text(c.get("comment_text") or "")
    first = text.split("\n", 1)[0]
    parts = [p.strip() for p in first.split("|")]
    company = parts[0][:80] if parts else ""
    title = parts[1] if len(parts) > 1 else first[:120]
    return _job(c["objectID"], title, company, " | ".join(parts[2:])[:200] if len(parts) > 2 else first[:200],
                f"https://news.ycombinator.com/item?id={c['objectID']}", (c.get("created_at") or "")[:10],
                f"[{story_title}] " + text, "")


def hn_whoishiring(months=1):
    stories = fetch_json("https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=12")
    hiring = [s for s in stories.get("hits", []) if "who is hiring" in s["title"].lower()][:months]
    out = []
    for s in hiring:
        res = fetch_json(f"https://hn.algolia.com/api/v1/search?tags=comment,story_{s['objectID']}&hitsPerPage=1000")
        for c in res.get("hits", []):
            if str(c.get("parent_id")) != str(s["objectID"]):
                continue  # replies, not postings
            j = _hn_comment_job(c, s["title"])
            if _relevant(j["title"], j["description"]):
                out.append(j)
    return out


# ------------------------------------------------- r/netsec quarterly thread
def reddit_netsec():
    # Reddit rate-limits back-to-back anonymous requests (HTTP 429), so the thread
    # found by search is cached for a week and the search is skipped meanwhile.
    from .registers import CACHE_DIR
    cache = CACHE_DIR / "reddit_netsec_thread.json"
    thread = None
    if cache.exists() and time.time() - cache.stat().st_mtime < 7 * 86400:
        thread = json.loads(cache.read_text(encoding="utf-8"))
    if not thread:
        threads = list(_rss_items("https://www.reddit.com/r/netsec/search.rss?q=hiring+thread&restrict_sr=1&sort=new"))
        thread = next(({"title": t["title"], "link": t["link"]} for t in threads
                       if "hiring" in t.get("title", "").lower()), None)
        if not thread:
            return []
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(thread), encoding="utf-8")
        time.sleep(15)
    link = thread["link"].rstrip("/") + "/.rss?limit=500"
    out = []
    try:
        entries = list(_rss_items(link))
    except FetchError:
        time.sleep(60)
        entries = list(_rss_items(link))
    for e in entries:
        text = html_to_text(e.get("content", ""))
        if not text or "hiring thread" in e.get("title", "").lower() and len(text) < 400:
            continue
        first = text.split("\n", 1)[0]
        parts = [p.strip() for p in re.split(r"\s*[|\-–]\s*", first) if p.strip()]
        company = parts[0][:80] if parts else ""
        out.append(_job(e.get("id") or e.get("link"), first[:140], company, first[:200], e.get("link"),
                        (e.get("updated") or "")[:10], f"[{thread['title']}] " + text, ""))
    return out


# --------------------------------------------------------------- Cyber Ireland
def cyber_ireland():
    return [_job(i.get("guid"), i.get("title"), i.get("company"), f"{i.get('location') or ''}, Ireland",
                 i.get("link"), _rss_date(i.get("pubDate")), html_to_text(i.get("encoded") or i.get("description")), "IE")
            for i in _rss_items("https://cyberireland.ie/?feed=job_feed")]


# ------------------------------------------------------- CyberSecurityJobsite
def cybersecurityjobsite(keywords=("security engineer", "penetration tester", "SOC analyst", "visa sponsorship",
                                   "automotive", "digital forensics")):
    out = {}
    for kw in keywords:
        for i in _rss_items(f"https://www.cybersecurityjobsite.com/jobsrss/?Keywords={quote_plus(kw)}"):
            company, _, title = (i.get("title") or "").partition(": ")
            if not title:
                company, title = "", company
            out[i.get("guid")] = _job(i.get("guid"), title, company, "United Kingdom", i.get("link"),
                                      _rss_date(i.get("pubDate")), html_to_text(i.get("description")), "GB")
    return list(out.values())


# ------------------------------------------------------------------- ISACA
def isaca():
    out = []
    for i in _rss_items("https://jobs.isaca.org/jobs/?display=rss"):
        title, _, company = (i.get("title") or "").rpartition(" | ")
        desc = html_to_text(i.get("description"))
        out.append(_job(i.get("guid"), title or i.get("title"), company, desc[:80], i.get("link"),
                        _rss_date(i.get("pubDate")), desc, ""))
    return out


# --------------------------------------------------------- Germany: Arbeitnow
def arbeitnow(pages=5):
    out = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    for _ in range(pages):
        data = fetch_json(url)
        for j in data.get("data", []):
            if not _relevant(j.get("title", "")):
                continue
            desc = html_to_text(j.get("description"))
            tags = j.get("tags") or []
            if any("visa" in t.lower() for t in tags):
                desc = "Visa sponsorship available (Arbeitnow tag). " + desc
            out.append(_job(j["slug"], j["title"], j.get("company_name"), j.get("location"), j.get("url"),
                            dt.datetime.fromtimestamp(j["created_at"]).date().isoformat() if j.get("created_at") else None,
                            desc, "DE"))
        url = (data.get("links") or {}).get("next")
        if not url:
            break
    return out


# ------------------------------------------- Germany: Bundesagentur für Arbeit
BA_QUERIES = ["Software Engineer", "Softwareentwickler", "Backend Developer", "Frontend Developer", "DevOps",
              "Data Engineer", "Data Scientist", "Machine Learning", "IT-Sicherheit", "Security Engineer",
              "Embedded Software", "Testautomatisierung", "Product Manager", "UX Designer",
              "Grafikdesigner", "Mediengestalter", "Motion Designer", "Video Editor", "Cutter",
              # Engineering
              "Maschinenbauingenieur", "Konstrukteur", "Verfahrenstechnik", "Mechanical Engineer",
              "Elektroingenieur", "Automatisierungstechnik", "Electrical Engineer", "Bauingenieur", "Tragwerksplanung",
              # Business
              "Marketing Manager", "Online Marketing", "Key Account Manager", "Sales Manager", "Controller",
              "Bilanzbuchhalter", "Financial Analyst", "Supply Chain", "Einkäufer", "Projektmanager",
              "HR Business Partner", "Recruiter",
              # Health
              "Pflegefachkraft", "Assistenzarzt", "Physiotherapeut", "Apotheker"]


def bundesagentur(queries=None, size=100):
    out = {}
    for q in queries or BA_QUERIES:
        data = fetch_json(
            f"https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs?was={quote_plus(q)}&size={size}&page=1",
            headers={"X-API-Key": "jobboerse-jobsuche"})
        for j in data.get("ergebnisliste", []) or []:
            # v6 renamed the v4 fields (refnr -> referenznummer, arbeitgeber -> firma, ...).
            ref = j.get("referenznummer") or j.get("refnr")
            if not ref or ref in out:
                continue
            title = j.get("stellenangebotsTitel") or j.get("titel") or ""
            company = j.get("firma") or j.get("arbeitgeber") or ""
            locs = j.get("stellenlokationen") or []
            loc = locs[0].get("adresse", {}) if locs else (j.get("arbeitsort") or {})
            out[ref] = _job(ref, title, company, f"{loc.get('ort', '')}, Germany",
                            f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{ref}",
                            (j.get("datumErsteVeroeffentlichung") or j.get("aktuelleVeroeffentlichungsdatum") or "")[:10] or None,
                            f"Beruf: {j.get('hauptberuf') or j.get('beruf') or ''}. Arbeitgeber: {company}. {title}", "DE")
    return list(out.values())


# ---------------------------------------------------- Germany: GermanTechJobs
def germantechjobs():
    out = []
    for i in _rss_items("https://germantechjobs.de/rss"):
        raw = i.get("title") or ""
        m = re.match(r"(.*?) @ (.*?)(?: \[(.*)\])?$", raw)
        title, company, salary = (m.group(1), m.group(2), m.group(3)) if m else (raw, "", None)
        if not _relevant(title):
            continue
        out.append(_job(i.get("guid"), title, company, "Germany", i.get("link"), _rss_date(i.get("pubDate")),
                        html_to_text(i.get("encoded") or i.get("description")), "DE", salary=salary))
    return out


# -------------------------------------------------------- Sweden: JobTech API
def jobtech(queries=("utvecklare", "software engineer", "devops", "data engineer", "security", "it-säkerhet", "embedded", "testare", "product manager", "ux",
                         "grafisk designer", "motion designer", "videoredigerare",
                         "maskiningenjör", "mechanical engineer", "elingenjör", "byggnadsingenjör", "civil engineer",
                         "marknadsförare", "marketing", "account manager", "säljare", "controller", "redovisningsekonom",
                         "supply chain", "inköpare", "projektledare", "hr", "rekryterare",
                         "sjuksköterska", "läkare", "fysioterapeut")):
    out = {}
    for q in queries:
        data = fetch_json(f"https://jobsearch.api.jobtechdev.se/search?q={quote_plus(q)}&limit=100")
        for h in data.get("hits", []):
            if h["id"] in out:
                continue
            addr = h.get("workplace_address") or {}
            out[h["id"]] = _job(h["id"], h.get("headline"), (h.get("employer") or {}).get("name"),
                                f"{addr.get('city') or addr.get('municipality') or ''}, Sweden", h.get("webpage_url"),
                                (h.get("publication_date") or "")[:10], (h.get("description") or {}).get("text", ""), "SE")
    return list(out.values())


# ------------------------------------------------------- Denmark: Jobindex
def jobindex(queries=("udvikler", "software engineer", "devops", "data engineer", "security", "sikkerhed", "grafisk designer", "video",
                          "maskiningeniør", "mechanical engineer", "elektroingeniør", "bygningsingeniør", "marketing", "sales",
                          "controller", "bogholder", "supply chain", "indkøber", "projektleder", "hr", "rekruttering",
                          "sygeplejerske", "læge")):
    out = {}
    for q in queries:
        for i in _rss_items(f"https://www.jobindex.dk/jobsoegning.rss?q={quote_plus(q)}"):
            title, _, company = (i.get("title") or "").rpartition(", ")
            out[i.get("guid")] = _job(i.get("guid"), title or i.get("title"), company, "Denmark", i.get("link"),
                                      _rss_date(i.get("pubDate")), html_to_text(i.get("description")), "DK")
    return list(out.values())


# ------------------------------------------------------------- Landing.jobs
def landingjobs(pages=3):
    out = []
    for p in range(pages):
        data = fetch_json(f"https://landing.jobs/api/v1/jobs?limit=50&offset={p * 50}")
        if not data:
            break
        for j in data:
            if not _relevant(j.get("title", "")):
                continue
            locs = j.get("locations") or []
            loc = " | ".join(", ".join(x for x in (l.get("city"), l.get("country_code")) if x) for l in locs)
            m = re.search(r"/at/([^/]+)/", j.get("url") or "")
            desc = html_to_text(" ".join(j.get(k) or "" for k in ("role_description", "main_requirements", "perks")))
            if j.get("relocation_paid"):
                desc = "Relocation package paid (Landing.jobs field). " + desc
            out.append(_job(j["id"], j["title"], m.group(1).replace("-", " ").title() if m else "", loc, j.get("url"),
                            (j.get("published_at") or "")[:10], desc, ""))
    return out


# ------------------------------------------------------------------ Relocate.me
def relocateme(terms=("software engineer", "backend", "frontend", "mobile", "data", "machine learning", "devops", "security", "qa", "product", "designer", "video", "motion",
                      "mechanical engineer", "electrical engineer", "civil engineer", "marketing", "sales", "finance", "accountant",
                      "supply chain", "project manager", "recruiter", "hr", "nurse")):
    out = {}
    for t in terms:
        page = fetch_text(f"https://relocate.me/search/{quote_plus(t)}")
        for href, inner in re.findall(r'href="(/[a-z-]+/[a-z-]+/[a-z0-9-]+/[a-z0-9-]+-\d+)"[^>]*>(.*?)</a>', page, re.S):
            title = html_to_text(inner).strip().split("\n")[0].strip()
            if not title or href in out:
                continue
            country, city, company = href.strip("/").split("/")[:3]
            out[href] = _job(href.rsplit("-", 1)[-1], title, company.replace("-", " ").title(),
                             f"{city.replace('-', ' ').title()}, {country.replace('-', ' ').title()}",
                             "https://relocate.me" + href, None,
                             "Relocation package offered (every Relocate.me listing includes relocation support).", "")
    return list(out.values())


# ------------------------------------------------------------------ Mastodon
def mastodon_tags(tags=("fedihire", "getfedihired", "techjobs", "securityjobs", "infosecjobs"), instance="mastodon.social"):
    out = {}
    for tag in tags:
        for i in _rss_items(f"https://{instance}/tags/{tag}.rss"):
            text = html_to_text(i.get("description"))
            if not _relevant(text[:160], text):
                continue
            out[i.get("guid")] = _job(i.get("guid"), text[:120], "", text[:200], i.get("link"),
                                      _rss_date(i.get("pubDate")), text, "")
    return list(out.values())


# ----------------------------------------------------- Singapore: MyCareersFuture
def mycareersfuture(queries=("software engineer", "developer", "data engineer", "devops", "cyber security", "product manager",
                            "graphic designer", "video editor", "motion designer",
                            "mechanical engineer", "electrical engineer", "civil engineer", "marketing", "sales", "accountant",
                            "financial analyst", "supply chain", "project manager", "human resources", "recruiter",
                            "nurse", "pharmacist", "physiotherapist")):
    """Singapore's government job portal (search API used by its own site). The
    Employment Pass needs roughly S$5,600+/month, so salary is shown for screening."""
    out = {}
    for q in queries:
        data = fetch_json("https://api.mycareersfuture.gov.sg/v2/search?limit=100&page=0",
                          data={"search": q, "sortBy": ["new_posting_date"]})
        for r in data.get("results", []):
            if r["uuid"] in out:
                continue
            meta = r.get("metadata") or {}
            sal = r.get("salary") or {}
            levels = ", ".join(p.get("position", "") for p in r.get("positionLevels") or [])
            company = (r.get("hiringCompany") or r.get("postedCompany") or {}).get("name", "")
            skills = ", ".join(s.get("skill", "") for s in (r.get("skills") or [])[:15])
            out[r["uuid"]] = _job(r["uuid"], r.get("title"), company, "Singapore", meta.get("jobDetailsUrl"),
                                  meta.get("newPostingDate"), f"Level: {levels}. Skills: {skills}.", "SG",
                                  salary=f"S${sal.get('minimum')}-{sal.get('maximum')}/month" if sal.get("minimum") else None)
    return list(out.values())


# ------------------------------------------------- Switzerland: swissdevjobs
def swissdevjobs_snapshot():
    """swissdevjobs.ch sits behind a Cloudflare browser challenge, so it can't be
    polled. This reads data/cache/swissdevjobs_snapshot.json, captured through the
    browser (ask Claude to refresh it). The site has a hasVisaSponsorship field."""
    from .registers import CACHE_DIR
    path = CACHE_DIR / "swissdevjobs_snapshot.json"
    if not path.exists():
        raise FetchError("no swissdevjobs snapshot yet (capture it through the browser)")
    snap = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for slug, title, company, city, visa, sfrom, sto, level, lang, active in snap["rows"]:
        facts = ["Visa sponsorship available (swissdevjobs field)." if visa else "No visa sponsorship flag on swissdevjobs.",
                 f"Language: {lang}. Level: {level}. Snapshot {snap['captured']}."]
        out.append(_job(slug, title, company, f"{city}, Switzerland", f"https://swissdevjobs.ch/jobs/{slug}",
                        active, " ".join(facts), "CH",
                        salary=f"CHF {sfrom:,}-{sto:,}" if sfrom and sto else None))
    return out



# ------------------------------------------------------------ EU: EURES portal
# The European Labour Authority's job-mobility portal aggregates the public
# employment services of the EU/EEA and Switzerland. Its legal notice allows
# re-use with attribution; europa.eu/robots.txt asks for a 10 s crawl delay.
# Searches are by ISCO occupation code, limited to ads that require English, so
# the job family comes from the official code, not from a title in any language.
EURES_COUNTRIES = ["de", "nl", "se", "dk", "fi", "ie", "lu", "ee", "pt", "es", "no", "ch"]
EURES_OCCUPATIONS = {
    "mechanical": ["C2144", "C2141", "C2145", "C3115"],   # mechanical, industrial/production, chemical engineers; mech. technicians
    "electrical": ["C2151", "C2152", "C3113"],           # electrical, electronics engineers; electrical technicians
    "civil": ["C2142", "C2161", "C3112"],                # civil engineers, architects, civil technicians
    "marketing": ["C2431", "C2432", "C1222"],            # marketing, PR professionals; advertising & PR managers
    "sales": ["C2433", "C2434", "C1221"],                # technical/medical and ICT sales professionals; sales managers
    "finance": ["C2411", "C2412", "C2413", "C1211"],     # accountants, financial advisers/analysts; finance managers
    "operations": ["C1324", "C2421", "C1219"],           # supply/logistics managers, management analysts
    "people": ["C2423", "C1212"],                        # personnel and careers professionals; HR managers
    "healthcare": ["C2221", "C2211", "C2212", "C2262", "C2264", "C2222"],  # nurses, doctors, pharmacists, physios, midwives
}


def eures(pages=2, per_page=50, delay=10):
    out = {}
    url = "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search"
    for family, codes in EURES_OCCUPATIONS.items():
        for page in range(1, pages + 1):
            body = {"resultsPerPage": per_page, "page": page, "sortSearch": "MOST_RECENT", "keywords": [],
                    "publicationPeriod": None, "occupationUris": [f"http://data.europa.eu/esco/isco/{c}" for c in codes],
                    "skillUris": [], "requiredExperienceCodes": [], "positionScheduleCodes": [], "sectorCodes": [],
                    "educationAndQualificationLevelCodes": [], "positionOfferingCodes": [], "locationCodes": EURES_COUNTRIES,
                    "euresFlagCodes": [], "otherBenefitsCodes": [], "requiredLanguages": [{"isoCode": "en", "level": "B2"}],
                    "minNumberPost": None, "sessionId": "visa-job-atlas"}
            data = fetch_json(url, data=body)
            time.sleep(delay)
            jvs = data.get("jvs") or []
            for v in jvs:
                if v["id"] in out:
                    continue
                countries = list((v.get("locationMap") or {}).keys())
                created = v.get("creationDate")
                posted = dt.datetime.fromtimestamp(int(created) / 1000, dt.timezone.utc).date().isoformat() if created else None
                desc = html_to_text(v.get("description") or "")
                if v.get("euresFlag"):
                    desc = "The employer recruits across borders through EURES (EURES flag). " + desc
                j = _job(v["id"], v.get("title"), (v.get("employer") or {}).get("name"), ", ".join(countries),
                         f"https://europa.eu/eures/portal/jv-se/jv-details/{v['id']}?lang=en", posted, desc,
                         countries[0] if len(countries) == 1 else "")
                j["family"] = family
                out[v["id"]] = j
            if len(jvs) < per_page:
                break
    return list(out.values())


# ------------------------------------------------------------- UK: NHS Jobs
# NHSBSA documents this XML search for websites that embed NHS vacancies. Every
# advert has a "Certificate of Sponsorship" section saying whether applicants who
# need a Skilled Worker visa are welcome; it is only on the advert page, so pages
# are fetched once per relevant advert (at most `max_details` a run) and cached.
NHS_CACHE = "nhsjobs_sponsorship.json"


def _nhs_sponsorship(page):
    i = page.find("Certificate of Sponsorship")
    if i < 0:
        return None
    section = html_to_text(page[i: i + 1500])
    if re.search(r"sponsorship[^.]{0,80}\b(are|is) welcome", section, re.I):
        return "yes"
    if re.search(r"\b(not|unable|cannot|can't)\b[^.]{0,80}sponsor", section, re.I):
        return "no"
    return None


def nhsjobs(pages=25, max_details=300, delay=1.0):
    from .registers import CACHE_DIR
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / NHS_CACHE
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    from .families import job_family
    out, details = [], 0
    for page in range(1, pages + 1):
        root = ET.fromstring(fetch(f"https://www.jobs.nhs.uk/api/v1/search_xml?limit=100&page={page}&sort=publicationDateDesc"))
        items = root.findall("vacancyDetails")
        for v in items:
            g = lambda tag: (v.findtext(tag) or "").strip()
            title, ref, link = g("title"), g("reference"), g("url")
            if not job_family(title):
                continue
            if ref not in cache and details < max_details:
                try:
                    cache[ref] = _nhs_sponsorship(fetch_text(link))
                except FetchError:
                    pass
                details += 1
                time.sleep(delay)
            desc = g("description")
            sponsor = cache.get(ref)
            if sponsor == "yes":
                desc = "Visa sponsorship available: applicants who need Skilled Worker sponsorship are welcome (NHS Jobs Certificate of Sponsorship field). " + desc
            elif sponsor == "no":
                desc = "This role does not offer visa sponsorship (NHS Jobs Certificate of Sponsorship field). " + desc
            locs = "; ".join(x.text or "" for x in v.iter("location"))
            out.append(_job(ref, title, g("employer"), f"{locs}, United Kingdom", link, g("postDate")[:10] or None,
                            desc, "GB", salary=g("salary") or None))
        if len(items) < 100:
            break
        time.sleep(delay)
    live = {j["ext_id"] for j in out}
    cache_path.write_text(json.dumps({k: v for k, v in cache.items() if k in live}), encoding="utf-8")
    return out



# ------------------------------------------------------- Berlin Startup Jobs
# English-speaking Berlin startups, all functions. Their terms allow crawlers;
# titles read "Role // Company".
BSJ_CATEGORIES = ["engineering", "sales", "marketing", "operations", "product-management", "design-ux",
                  "hr-recruiting", "finance"]


def berlinstartupjobs():
    out = {}
    for cat in BSJ_CATEGORIES:
        for i in _rss_items(f"https://berlinstartupjobs.com/{cat}/feed/"):
            title, _, company = (i.get("title") or "").partition(" // ")
            out[i.get("link")] = _job(i.get("guid") or i.get("link"), html.unescape(title), html.unescape(company), "Berlin, Germany",
                                      i.get("link"), _rss_date(i.get("pubDate")),
                                      html_to_text(i.get("encoded") or i.get("description")), "DE")
        time.sleep(1)
    return list(out.values())



FEEDS = {
    "swissdevjobs_snapshot": swissdevjobs_snapshot,
    "mycareersfuture": mycareersfuture,
    "japandev": japandev,
    "tokyodev": tokyodev,
    "hn_whoishiring": hn_whoishiring,
    "reddit_netsec": reddit_netsec,
    "cyber_ireland": cyber_ireland,
    "cybersecurityjobsite": cybersecurityjobsite,
    "isaca": isaca,
    "arbeitnow": arbeitnow,
    "bundesagentur": bundesagentur,
    "germantechjobs": germantechjobs,
    "jobtech": jobtech,
    "jobindex": jobindex,
    "landingjobs": landingjobs,
    "relocateme": relocateme,
    "mastodon": mastodon_tags,
    "eures": eures,
    "nhsjobs": nhsjobs,
    "berlinstartupjobs": berlinstartupjobs,
}
