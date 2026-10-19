"""Public applicant-tracking-system (ATS) job-board APIs.

All endpoints here are keyless, public read APIs that employers expose for
their own careers pages. Each fetcher returns normalised job dicts:

    {"ext_id", "title", "location", "url", "posted_at", "department",
     "remote", "salary", "description"}

`description` may be None for boards where it costs one request per job
(SmartRecruiters, Personio); call `fetch_description` for the shortlisted ones.
"""

import datetime as dt
import html
import re
import xml.etree.ElementTree as ET

from .http import FetchError, fetch, fetch_json

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t\r\f\v]+")


def html_to_text(s):
    if not s:
        return ""
    s = html.unescape(s)  # Greenhouse double-escapes its HTML
    s = re.sub(r"(?i)<\s*(br|/p|/li|/h\d|/div)\s*/?>", "\n", s)
    s = _TAG.sub(" ", s)
    s = html.unescape(s)
    return "\n".join(_WS.sub(" ", line).strip() for line in s.splitlines() if line.strip())


def _iso_from_ms(ms):
    try:
        return dt.datetime.fromtimestamp(int(ms) / 1000, dt.timezone.utc).date().isoformat()
    except (TypeError, ValueError):
        return None


def _date(s):
    return s[:10] if isinstance(s, str) and len(s) >= 10 else None


# ----------------------------------------------------------------- Greenhouse
def greenhouse(slug):
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true")
    out = []
    for j in data.get("jobs", []):
        locs = [j.get("location", {}).get("name") or ""]
        locs += [o.get("location") or o.get("name") or "" for o in j.get("offices", [])]
        out.append({
            "ext_id": str(j["id"]),
            "title": j.get("title", ""),
            "location": " | ".join(dict.fromkeys(l for l in locs if l)),
            "url": j.get("absolute_url"),
            "posted_at": _date(j.get("first_published") or j.get("updated_at")),
            "department": ", ".join(d.get("name", "") for d in j.get("departments", [])),
            "remote": None,
            "salary": None,
            "description": html_to_text(j.get("content")),
        })
    return out


# ---------------------------------------------------------------------- Lever
def lever(slug):
    data = None
    for host in ("api.lever.co", "api.eu.lever.co"):
        try:
            data = fetch_json(f"https://{host}/v0/postings/{slug}?mode=json")
        except FetchError:
            continue
        if isinstance(data, list) and data:
            break
    if not isinstance(data, list):
        raise FetchError(f"lever board '{slug}' not found on US or EU host")
    out = []
    for j in data:
        cats = j.get("categories") or {}
        locs = cats.get("allLocations") or [cats.get("location") or ""]
        desc = [j.get("descriptionPlain") or ""]
        for lst in j.get("lists") or []:
            desc.append(lst.get("text", ""))
            desc.append(html_to_text(lst.get("content", "")))
        desc.append(j.get("additionalPlain") or "")
        sal = j.get("salaryRange") or {}
        out.append({
            "ext_id": j["id"],
            "title": j.get("text", ""),
            "location": " | ".join(l for l in locs if l) + (f" ({j['country']})" if j.get("country") else ""),
            "url": j.get("hostedUrl"),
            "posted_at": _iso_from_ms(j.get("createdAt")),
            "department": cats.get("team") or cats.get("department") or "",
            "remote": (j.get("workplaceType") == "remote") if j.get("workplaceType") else None,
            "salary": f"{sal.get('min')}-{sal.get('max')} {sal.get('currency', '')} {sal.get('interval', '')}".strip() if sal else None,
            "description": "\n".join(d for d in desc if d),
        })
    return out


# ---------------------------------------------------------------------- Ashby
def ashby(slug):
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    out = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        country = ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry")
        comp = (j.get("compensation") or {}).get("compensationTierSummary")
        out.append({
            "ext_id": j["id"],
            "title": j.get("title", ""),
            "location": " | ".join(dict.fromkeys(l for l in locs if l)) + (f" ({country})" if country else ""),
            "url": j.get("jobUrl"),
            "posted_at": _date(j.get("publishedAt")),
            "department": j.get("department") or j.get("team") or "",
            "remote": j.get("isRemote"),
            "salary": comp,
            "description": j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml")),
        })
    return out


# ------------------------------------------------------------ SmartRecruiters
def smartrecruiters(slug, query=None):
    """`query` narrows very large boards (e.g. BoschGroup) server-side."""
    from urllib.parse import quote_plus
    q = f"&q={quote_plus(query)}" if query else ""
    out, offset = [], 0
    while True:
        data = fetch_json(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=100&offset={offset}{q}")
        content = data.get("content", [])
        for j in content:
            loc = j.get("location") or {}
            out.append({
                "ext_id": str(j["id"]),
                "title": j.get("name", ""),
                "location": loc.get("fullLocation") or ", ".join(x for x in (loc.get("city"), loc.get("region"), (loc.get("country") or "").upper()) if x),
                "url": f"https://jobs.smartrecruiters.com/{slug}/{j['id']}",
                "posted_at": _date(j.get("releasedDate")),
                "department": (j.get("department") or {}).get("label", ""),
                "remote": loc.get("remote"),
                "salary": None,
                "description": None,
                "_detail": f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{j['id']}",
            })
        offset += len(content)
        if not content or offset >= data.get("totalFound", 0) or offset >= 2000:
            break
    return out


# ------------------------------------------------------------------- Workable
def workable(slug):
    data = fetch_json(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    out = []
    for j in data.get("jobs", []):
        locs = [", ".join(x for x in (l.get("city"), l.get("country")) if x) for l in j.get("locations") or []]
        if not locs:
            locs = [", ".join(x for x in (j.get("city"), j.get("country")) if x)]
        out.append({
            "ext_id": j.get("shortcode") or j.get("id"),
            "title": j.get("title", ""),
            "location": " | ".join(l for l in locs if l),
            "url": j.get("url") or j.get("shortlink"),
            "posted_at": _date(j.get("published_on") or j.get("created_at")),
            "department": j.get("department") or "",
            "remote": j.get("telecommuting"),
            "salary": None,
            "description": html_to_text(j.get("description")),
        })
    return out


# ------------------------------------------------------------------ Recruitee
def recruitee(slug):
    data = fetch_json(f"https://{slug}.recruitee.com/api/offers/")
    out = []
    for j in data.get("offers", []):
        out.append({
            "ext_id": str(j["id"]),
            "title": j.get("title", ""),
            "location": j.get("location") or ", ".join(x for x in (j.get("city"), j.get("country")) if x),
            "url": j.get("careers_url"),
            "posted_at": _date(j.get("published_at") or j.get("created_at")),
            "department": j.get("department") or "",
            "remote": j.get("remote"),
            "salary": None,
            "description": html_to_text((j.get("description") or "") + " " + (j.get("requirements") or "")),
        })
    return out


# ------------------------------------------------------------------- Personio
def personio(slug):
    body = fetch(f"https://{slug}.jobs.personio.de/xml?language=en")
    root = ET.fromstring(body)
    out = []
    for p in root.iter("position"):
        get = lambda tag: (p.findtext(tag) or "").strip()
        desc = " ".join(html_to_text(d.findtext("value") or "") for d in p.iter("jobDescription"))
        offices = [get("office")] + [o.text or "" for o in p.iter("additionalOffice")]
        out.append({
            "ext_id": get("id"),
            "title": get("name"),
            "location": " | ".join(o for o in offices if o),
            "url": f"https://{slug}.jobs.personio.de/job/{get('id')}",
            "posted_at": _date(get("createdAt")),
            "department": get("department"),
            "remote": None,
            "salary": None,
            "description": desc,
        })
    return out


# --------------------------------------------------------------------- Amazon
def _amazon_date(s):
    try:
        return dt.datetime.strptime(s, "%B %d, %Y").date().isoformat()
    except (TypeError, ValueError):
        return None


def amazon(query, limit=500):
    """amazon.jobs search JSON. `query` is a search string (e.g. 'security engineer'),
    since the full board is ~10k+ roles. Newest first, capped at `limit`."""
    from urllib.parse import quote_plus
    out, offset = [], 0
    while offset < limit:
        data = fetch_json(f"https://www.amazon.jobs/en/search.json?base_query={quote_plus(query)}"
                          f"&result_limit=100&offset={offset}&sort=recent")
        batch = data.get("jobs", [])
        for j in batch:
            out.append({
                "ext_id": str(j.get("id_icims") or j.get("id")),
                "title": j.get("title", ""),
                "location": f"{j.get('normalized_location') or j.get('location') or ''} ({j.get('country_code', '')})",
                "url": "https://www.amazon.jobs" + (j.get("job_path") or ""),
                "posted_at": _amazon_date(j.get("posted_date")),
                "department": j.get("business_category") or "",
                "remote": None,
                "salary": None,
                "description": html_to_text(" ".join(j.get(k) or "" for k in
                                                     ("description", "basic_qualifications", "preferred_qualifications"))),
                "entity": j.get("company_name"),
            })
        offset += len(batch)
        if not batch or offset >= data.get("hits", 0):
            break
    return out


# -------------------------------------------------------------------- Workday
def workday(slug, query="security", limit=400):
    """Workday's careers-site JSON (the same calls its own job search page makes).
    slug = "host|tenant|site", e.g. "aptiv.wd5.myworkdayjobs.com|aptiv|APTIV_CAREERS"."""
    host, tenant, site = slug.split("|")
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    out, offset, total = [], 0, None
    while offset < limit:
        data = fetch_json(f"{base}/jobs", data={"appliedFacets": {}, "limit": 20, "offset": offset,
                                                "searchText": query or ""})
        posts = data.get("jobPostings") or []
        if total is None:
            total = data.get("total") or 0  # only the first page reports the total
        for p in posts:
            path = p.get("externalPath") or ""
            out.append({
                "ext_id": path.rsplit("_", 1)[-1] if "_" in path else path,
                "title": p.get("title", ""),
                "location": p.get("locationsText") or "",
                "url": f"https://{host}/en-US/{site}{path}",
                "posted_at": None,
                "department": "",
                "remote": None,
                "salary": None,
                "description": None,
                "_detail": f"{base}{path}",
                "_detail_kind": "workday",
            })
        offset += len(posts)
        if not posts or offset >= total:
            break
    return out


def _workday_detail(job):
    d = fetch_json(job["_detail"]).get("jobPostingInfo") or {}
    country = (d.get("country") or {}).get("descriptor")
    if country and country not in job["location"]:
        job["location"] = f"{job['location']} ({country})" if job["location"] else country
    if d.get("location") and "Locations" in job["location"]:
        job["location"] = d["location"] + (f" ({country})" if country else "")
    job["posted_at"] = (d.get("startDate") or "")[:10] or None
    return html_to_text(d.get("jobDescription"))


# ------------------------------------------------------- Microsoft and Google
def microsoft(query="security", limit=150):
    """Microsoft's careers search JSON (apply.careers.microsoft.com, the API behind
    its job search page). Newest first, 10 per page, capped at `limit`. It returns
    HTTP 429 when paged quickly, so pages are spaced out and a 429 ends the run
    with what was collected."""
    import time
    from urllib.parse import quote_plus
    out, start = [], 0
    while start < limit:
        if start:
            time.sleep(3)
        try:
            data = fetch_json(f"https://apply.careers.microsoft.com/api/pcsx/search?domain=microsoft.com"
                              f"&query={quote_plus(query)}&start={start}").get("data") or {}
        except FetchError:
            if out:
                break
            raise
        batch = data.get("positions") or []
        for p in batch:
            ts = p.get("postedTs") or p.get("creationTs")
            out.append({
                "ext_id": str(p.get("displayJobId") or p.get("id")),
                "title": p.get("name", ""),
                "location": " | ".join(p.get("locations") or []),
                "url": p.get("positionUrl") if (p.get("positionUrl") or "").startswith("http")
                       else f"https://apply.careers.microsoft.com/careers/job/{p.get('id')}",
                "posted_at": dt.datetime.fromtimestamp(ts, dt.timezone.utc).date().isoformat() if ts else None,
                "department": p.get("department") or "",
                "remote": None, "salary": None, "description": "",
            })
        start += len(batch)
        if not batch or start >= (data.get("count") or 0):
            break
    return out


def google(query="security", pages=10):
    """Google careers results pages are server-rendered; titles are <h3 class="QJPWVe">
    and locations <span class="r0wTof">. No description (one request per job)."""
    from urllib.parse import quote_plus
    out, seen = [], set()
    for page in range(1, pages + 1):
        h = fetch(f"https://www.google.com/about/careers/applications/jobs/results/?q={quote_plus(query)}"
                  f"&sort_by=date&page={page}").decode("utf-8", "replace")
        parts = h.split('<h3 class="QJPWVe">')
        if len(parts) < 2:
            break
        for prev, seg in zip(parts, parts[1:]):
            title = html.unescape(seg.split("<", 1)[0]).strip()
            locs = [html.unescape(x).strip() for x in re.findall(r'class="r0wTof ?">([^<]+)<', seg.split('<h3 class="QJPWVe">')[0])]
            m = re.search(r'jobs/results/(\d+)-([a-z0-9-]+)', seg) or re.search(r'jobs/results/(\d+)-([a-z0-9-]+)', prev[-3000:])
            if not m or m.group(1) in seen:
                continue
            seen.add(m.group(1))
            out.append({
                "ext_id": m.group(1), "title": title, "location": " | ".join(dict.fromkeys(locs)),
                "url": f"https://www.google.com/about/careers/applications/jobs/results/{m.group(1)}-{m.group(2)}",
                "posted_at": None, "department": "", "remote": None, "salary": None, "description": "",
            })
    return out


FETCHERS = {
    "microsoft": microsoft,
    "google": google,
    "workday": workday,
    "amazon": amazon,
    "greenhouse": greenhouse,
    "lever": lever,
    "ashby": ashby,
    "smartrecruiters": smartrecruiters,
    "workable": workable,
    "recruitee": recruitee,
    "personio": personio,
}


def fetch_description(job):
    """Fill in the description for boards that need a per-job request."""
    if job.get("description") is not None or not job.get("_detail"):
        return job
    if job.get("_detail_kind") == "workday":
        try:
            job["description"] = _workday_detail(job)
        except FetchError:
            job["description"] = ""
        return job
    try:
        d = fetch_json(job["_detail"])
        sections = (d.get("jobAd") or {}).get("sections") or {}
        job["description"] = "\n".join(html_to_text(s.get("text", "")) for s in sections.values() if isinstance(s, dict))
    except FetchError:
        job["description"] = ""
    return job


def discover(name):
    """Try likely slugs for a company name on every ATS; return hits."""
    base = re.sub(r"[^a-z0-9]+", "", name.lower())
    dashed = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    candidates = list(dict.fromkeys([base, dashed, base + "inc", base + "hq", base + "careers", base + "jobs"]))
    hits = []
    for ats, fn in FETCHERS.items():
        if ats in ("amazon", "workday", "microsoft", "google"):
            continue
        for slug in candidates:
            if ats == "smartrecruiters":
                slug = name.replace(" ", "")
            try:
                jobs = fn(slug)
            except Exception:
                continue
            if jobs:
                hits.append((ats, slug, len(jobs)))
                break
    return hits
