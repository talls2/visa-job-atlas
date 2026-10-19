"""Government sponsor-register loaders.

Each loader returns a list of dicts:
    {"country": ISO2, "source": str, "name": legal entity, "weight": float, "detail": str}
Weight is source-specific evidence strength (permits issued, LMIA positions,
or 1 for "licensed/recognised"). Raw downloads are cached under data/cache.
"""

import csv
import datetime as dt
import gzip
import html
import io
import json
import re
from collections import defaultdict
from pathlib import Path

from . import xlsx
from .http import FetchError, fetch, fetch_json, fetch_text

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
BUNDLED_DIR = Path(__file__).resolve().parent.parent / "registers"
MAX_AGE_DAYS = 6


def _cached(key, url_or_fn, force=False):
    """Download once per MAX_AGE_DAYS; url_or_fn may resolve the URL lazily."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / key
    if path.exists() and not force:
        age = dt.datetime.now() - dt.datetime.fromtimestamp(path.stat().st_mtime)
        if age.days < MAX_AGE_DAYS:
            return path.read_bytes()
    try:
        url = url_or_fn() if callable(url_or_fn) else url_or_fn
        data = fetch(url, timeout=180)
    except Exception:
        # Some government sites block cloud runners (USCIS returns 403 to
        # GitHub Actions). Fall back to the last download, then to the copy
        # bundled in pipeline/registers/.
        if path.exists():
            return path.read_bytes()
        bundled = BUNDLED_DIR / (key + ".gz")
        if bundled.exists():
            return gzip.decompress(bundled.read_bytes())
        raise
    path.write_bytes(data)
    return data


# --------------------------------------------------------------------------- UK
UK_CONTENT_API = "https://www.gov.uk/api/content/government/publications/register-of-licensed-sponsors-workers"
UK_SPONSOR_ROUTES = ("Skilled Worker", "Global Business Mobility", "Scale-up")


def _uk_csv_url():
    meta = fetch_json(UK_CONTENT_API)
    for att in meta.get("details", {}).get("attachments", []):
        if att.get("content_type", "").startswith("text/csv") or att.get("url", "").endswith(".csv"):
            return att["url"]
    raise FetchError("UK register CSV link not found in GOV.UK content API")


def load_uk(force=False):
    data = _cached("uk_sponsors.csv", _uk_csv_url, force)
    agg = defaultdict(lambda: {"routes": set(), "ratings": set(), "towns": set()})
    for row in csv.DictReader(io.StringIO(data.decode("utf-8-sig", "replace"))):
        route = (row.get("Route") or "").strip()
        if not route.startswith(UK_SPONSOR_ROUTES):
            continue
        name = (row.get("Organisation Name") or "").strip()
        a = agg[name]
        a["routes"].add(route)
        a["ratings"].add((row.get("Type & Rating") or "").strip())
        if row.get("Town/City"):
            a["towns"].add(row["Town/City"].strip().title())
    out = []
    for name, a in agg.items():
        rating = "B rating" if any("B rating" in r for r in a["ratings"]) else "A rating"
        out.append({
            "country": "GB", "source": "uk_sponsor_register", "name": name,
            "weight": 1.0 if rating == "A rating" else 0.5,
            "detail": f"UK licensed sponsor ({', '.join(sorted(a['routes']))}; {rating}; {', '.join(sorted(a['towns'])[:2])})",
        })
    return out


# ---------------------------------------------------------------------- Ireland
DETE_PAGE = "https://enterprise.gov.ie/en/publications/employment-permit-statistics-{year}.html"


def _dete_url(year):
    def resolve():
        page = fetch_text(DETE_PAGE.format(year=year))
        m = re.search(r'href="([^"]*issued-to-companies-%d\.xlsx)"' % year, page)
        if not m:
            raise FetchError(f"DETE companies file for {year} not linked yet")
        return "https://enterprise.gov.ie" + m.group(1) if m.group(1).startswith("/") else m.group(1)
    return resolve


def load_ie(force=False, years=None):
    this_year = dt.date.today().year
    years = years or (this_year, this_year - 1)
    totals = defaultdict(dict)
    for year in years:
        try:
            data = _cached(f"ie_permits_{year}.xlsx", _dete_url(year), force)
        except FetchError:
            continue
        rows = xlsx.iter_rows(data)
        header = next(rows, [])
        try:
            name_i = next(i for i, h in enumerate(header) if "employer" in h.lower())
            total_i = next(i for i, h in enumerate(header) if "total" in h.lower())
        except StopIteration:
            continue
        months = sum(1 for h in header if h.lower().startswith("permits issued") and "total" not in h.lower())
        for row in rows:
            if len(row) <= total_i or not row[name_i].strip():
                continue
            try:
                n = float(row[total_i] or 0)
            except ValueError:
                continue
            totals[row[name_i].strip()][year] = (n, months)
    out = []
    for name, by_year in totals.items():
        latest = max(by_year)
        n, months = by_year[latest]
        parts = [f"{int(v[0])} in {y}" + (f" ({v[1]} months)" if y == this_year else "") for y, v in sorted(by_year.items(), reverse=True)]
        out.append({
            "country": "IE", "source": "ie_dete_permits", "name": name,
            "weight": n, "detail": "Irish employment permits issued: " + ", ".join(parts),
        })
    return out


# ----------------------------------------------------------------------- Canada
CA_PACKAGE = "https://open.canada.ca/data/api/action/package_show?id=90fed587-1364-4f33-a9ee-208181dc0b97"
# NOC 2021 codes for computer/information-systems work; 21220 = cybersecurity specialists.
CA_TECH_NOC = re.compile(r"^(212\d\d|2222\d|2131\d)")
CA_CYBER_NOC = "21220"


def load_ca(force=False, quarters=4):
    pkg = fetch_json(CA_PACKAGE)
    res = [
        r for r in pkg["result"]["resources"]
        if "en" in (r.get("language") or []) and (r.get("format") or "").upper() == "XLSX"
        and re.search(r"(20\d\d)Q([1-4])", r.get("name") or "")
    ]
    res.sort(key=lambda r: re.search(r"(20\d\d)Q([1-4])", r["name"]).groups())
    agg = defaultdict(lambda: {"pos": 0, "cyber": 0, "streams": set(), "quarters": set(), "cities": set()})
    for r in res[-quarters:]:
        q = "%sQ%s" % re.search(r"(20\d\d)Q([1-4])", r["name"]).groups()
        data = _cached(f"ca_lmia_{q}.xlsx", r["url"], force)
        header = None
        for row in xlsx.iter_rows(data):
            if header is None:
                if "Employer" in row and "Occupation" in row:
                    header = {h: i for i, h in enumerate(row)}
                continue
            if len(row) < len(header):
                continue
            occ = row[header["Occupation"]].strip()
            if not CA_TECH_NOC.match(occ):
                continue
            name = row[header["Employer"]].strip()
            try:
                pos = int(float(row[header.get("Approved Positions", -1)] or 0))
            except (ValueError, IndexError):
                pos = 0
            a = agg[name]
            a["pos"] += pos
            if occ.startswith(CA_CYBER_NOC):
                a["cyber"] += pos
            a["streams"].add(row[header["Program Stream"]].strip())
            a["quarters"].add(q)
            city = row[header["Address"]].split(",")[0].strip().title() if "Address" in header else ""
            if city:
                a["cities"].add(city)
    out = []
    for name, a in agg.items():
        cyber = f", {a['cyber']} cybersecurity (NOC 21220)" if a["cyber"] else ""
        out.append({
            "country": "CA", "source": "ca_lmia_positive", "name": name, "weight": float(a["pos"]),
            "detail": f"Positive LMIAs for tech roles: {a['pos']} positions{cyber}; {', '.join(sorted(a['streams']))}; "
                      f"{', '.join(sorted(a['quarters']))}; {', '.join(sorted(a['cities'])[:2])}",
        })
    return out


# ------------------------------------------------------------------ Netherlands
IND_WORK = "https://ind.nl/en/public-register-recognised-sponsors/public-register-work"


def load_nl(force=False):
    page = _cached("nl_ind_work.html", IND_WORK, force).decode("utf-8", "replace")
    out = []
    for name, kvk in re.findall(r'<th scope="row">(.*?)</th>\s*<td>(\d+)</td>', page, re.S):
        name = html.unescape(re.sub(r"<.*?>", "", name)).strip().strip('"').replace('""', '"')
        out.append({
            "country": "NL", "source": "nl_ind_recognised_sponsor", "name": name, "weight": 1.0,
            "detail": f"IND recognised sponsor (labour), KvK {kvk}",
        })
    return out


# ---------------------------------------------------------------------- Denmark
SIRI_PAGE = "https://www.nyidanmark.dk/en-GB/Words-and-concepts/SIRI/Certified-companies"


def load_dk(force=False):
    page = _cached("dk_siri_certified.html", SIRI_PAGE, force).decode("utf-8", "replace")
    out, seen = [], set()
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        cells = [html.unescape(re.sub(r"<.*?>", "", c)).replace("\xa0", " ").strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) >= 2 and re.fullmatch(r"\d{8}", cells[1]) and cells[0] and cells[0] not in seen:
            seen.add(cells[0])
            out.append({
                "country": "DK", "source": "dk_siri_fast_track", "name": cells[0], "weight": 1.0,
                "detail": f"SIRI Fast-track certified company, CVR {cells[1]}",
            })
    return out


# ------------------------------------------------------------------ United States
# DOL's LCA disclosure files sit behind bot protection (HTTP 403), so the US
# source is USCIS's H-1B Employer Data Hub CSV export. USCIS stopped posting
# yearly CSVs after FY2023, so this shows sponsorship history, not this year.
USCIS_FILES = "https://www.uscis.gov/tools/reports-and-studies/h-1b-employer-data-hub/h-1b-employer-data-hub-files"


def _uscis_latest_url():
    page = fetch_text(USCIS_FILES)
    links = sorted(set(re.findall(r'href="([^"]*h1b_datahubexport-(\d{4})\.csv)"', page)), key=lambda x: x[1])
    if not links:
        raise FetchError("USCIS H-1B export links not found")
    return "https://www.uscis.gov" + links[-1][0]


def load_us(force=False):
    url = _uscis_latest_url()
    year = re.search(r"(\d{4})\.csv", url).group(1)
    data = _cached(f"us_h1b_{year}.csv", url, force)
    agg = defaultdict(lambda: {"initial": 0, "continuing": 0, "cities": set()})
    for row in csv.DictReader(io.StringIO(data.decode("utf-8-sig", "replace"))):
        name = (row.get("Employer") or "").strip()
        if not name:
            continue
        a = agg[name]
        try:
            a["initial"] += int(row.get("Initial Approval") or 0)
            a["continuing"] += int(row.get("Continuing Approval") or 0)
        except ValueError:
            continue
        if row.get("City"):
            a["cities"].add(row["City"].strip().title())
    out = []
    for name, a in agg.items():
        total = a["initial"] + a["continuing"]
        if total == 0:
            continue
        out.append({
            "country": "US", "source": "us_uscis_h1b", "name": name, "weight": float(total),
            "detail": f"H-1B approvals FY{year}: {a['initial']} initial, {a['continuing']} continuing; "
                      f"{', '.join(sorted(a['cities'])[:2])}",
        })
    return out


LOADERS = {"uk": load_uk, "ie": load_ie, "ca": load_ca, "nl": load_nl, "dk": load_dk, "us": load_us}
