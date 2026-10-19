"""Country detection, seniority and visa-signal extraction.

Visa rule (from the research report): a posting is likely sponsored if its text
states sponsorship/relocation, or the employer has register filings in that
country; negative phrases ("must have the right to work", "clearance",
"EU citizen"...) override both. Personal fit is scored in the browser, not here.
"""

import re

from .families import job_family

# Older name kept for the feeds module.
role_tier = job_family


SENIORITY = [
    ("intern", re.compile(r"\b(intern|internship|praktikum|working student|werkstudent)\b", re.I)),
    ("new-grad", re.compile(r"\b(new grad|graduate|entry[- ]level|early career|university)\b", re.I)),
    ("junior", re.compile(r"\b(junior|jr\.?|associate)\b", re.I)),
    ("principal", re.compile(r"\b(principal|distinguished|fellow)\b", re.I)),
    ("staff", re.compile(r"\bstaff\b", re.I)),
    ("manager", re.compile(r"\b(manager|head of|director|vp|vice president|chief|ciso)\b", re.I)),
    ("lead", re.compile(r"\b(lead|tech lead)\b", re.I)),
    ("senior", re.compile(r"\b(senior|sr\.?|iii|iv)\b", re.I)),
]


def seniority(title):
    for label, rx in SENIORITY:
        if rx.search(title or ""):
            return label
    return "unspecified"  # title gives no level; read the posting's experience requirement


# ------------------------------------------------------------------- countries
_COUNTRY_WORDS = {
    "US": ["united states", "usa", "u.s.", "new york", "nyc", "san francisco", "seattle", "austin", "boston",
           "chicago", "denver", "los angeles", "washington, dc", "washington dc", "atlanta", "miami", "dallas",
           "houston", "san jose", "palo alto", "mountain view", "sunnyvale", "menlo park", "redmond", "portland",
           "pittsburgh", "philadelphia", "raleigh", "salt lake", "phoenix", "san diego", "arlington", "reston",
           "minneapolis", "nashville", "remote - us", "remote, us", "us remote", "us-remote"],
    "CA": ["canada", "toronto", "vancouver", "montreal", "montréal", "ottawa", "waterloo", "calgary", "edmonton"],
    "GB": ["united kingdom", "uk", "england", "scotland", "wales", "london", "manchester", "edinburgh", "cardiff",
           "bristol", "cambridge, uk", "oxford", "belfast", "leeds", "glasgow", "reading"],
    "IE": ["ireland", "dublin", "cork", "galway", "limerick"],
    "NL": ["netherlands", "amsterdam", "rotterdam", "utrecht", "eindhoven", "the hague", "den haag", "delft"],
    "DE": ["germany", "deutschland", "berlin", "munich", "münchen", "hamburg", "frankfurt", "cologne", "köln",
           "stuttgart", "düsseldorf", "dusseldorf", "karlsruhe", "leipzig"],
    "CH": ["switzerland", "zurich", "zürich", "geneva", "genève", "lausanne", "basel", "bern", "zug", "lugano"],
    "JP": ["japan", "tokyo", "osaka", "kyoto", "fukuoka", "yokohama"],
    "SE": ["sweden", "stockholm", "gothenburg", "göteborg", "malmö", "malmo"],
    "DK": ["denmark", "copenhagen", "københavn", "aarhus"],
    "FI": ["finland", "helsinki", "espoo", "tampere", "oulu"],
    "NO": ["norway", "oslo", "bergen", "trondheim"],
    "AU": ["australia", "sydney", "melbourne", "brisbane", "perth", "canberra", "adelaide"],
    "NZ": ["new zealand", "auckland", "wellington"],
    "SG": ["singapore"],
    "AE": ["united arab emirates", "uae", "dubai", "abu dhabi"],
    "LU": ["luxembourg"],
    "EE": ["estonia", "tallinn"],
    "FR": ["france", "paris"],
    "ES": ["spain", "madrid", "barcelona"],
    "PT": ["portugal", "lisbon", "lisboa", "porto"],
    "PL": ["poland", "warsaw", "kraków", "krakow"],
    "KR": ["south korea", "korea", "seoul"],
    "TW": ["taiwan", "taipei"],
    "IN": ["india", "bangalore", "bengaluru", "hyderabad", "pune", "gurgaon", "noida", "chennai"],
    "BR": ["brazil", "brasil", "são paulo", "sao paulo"],
}
_ISO_CODES = {"US", "CA", "GB", "IE", "NL", "DE", "CH", "JP", "SE", "DK", "FI", "NO", "AU", "NZ", "SG", "AE",
              "LU", "EE", "FR", "ES", "PT", "PL", "KR", "TW", "IN", "BR"}
_ISO3 = {"USA": "US", "GBR": "GB", "IRL": "IE", "NLD": "NL", "DEU": "DE", "CHE": "CH", "JPN": "JP", "CAN": "CA",
         "SWE": "SE", "DNK": "DK", "FIN": "FI", "NOR": "NO", "AUS": "AU", "SGP": "SG", "ARE": "AE"}
_COUNTRY_RX = {
    iso: re.compile(r"(?<![a-z])(" + "|".join(re.escape(w) for w in words) + r")(?![a-z])", re.I)
    for iso, words in _COUNTRY_WORDS.items()
}
_US_STATE = re.compile(r",\s*(CA|NY|WA|TX|MA|IL|CO|GA|FL|VA|NC|OR|PA|UT|AZ|MN|NJ|DC|MD|OH|MI|TN)\b")
REMOTE_RX = re.compile(r"\bremote\b|\banywhere\b|\bdistributed\b", re.I)


# Upper-case country tokens that are unambiguous in a location string ("Remote US",
# "Dublin, IRL", "Ontario, CAN"). Two-letter "CA" is skipped: it usually means California.
_UPPER_TOKENS = {"US": "US", "USA": "US", "UK": "GB", "UAE": "AE", "IRL": "IE", "CAN": "CA", "AUS": "AU",
                 "GBR": "GB", "DEU": "DE", "NLD": "NL", "CHE": "CH", "JPN": "JP", "SGP": "SG", "SWE": "SE",
                 "DNK": "DK", "FIN": "FI", "NOR": "NO", "NZL": "NZ", "ARE": "AE", "IE": "IE", "NL": "NL",
                 "DE": "DE", "JP": "JP", "SG": "SG", "GB": "GB", "AU": "AU"}


def countries(location):
    """Best-effort set of ISO-2 codes mentioned in a location string."""
    loc = (location or "").replace("New South Wales", "NSW").replace("new south wales", "NSW")
    found = {iso for iso, rx in _COUNTRY_RX.items() if rx.search(loc)}
    for code in re.findall(r"\(([A-Z]{2,3})\)", loc):
        code = _ISO3.get(code, code)
        if code in _ISO_CODES:
            found.add(code)
    for tok in re.findall(r"(?<![A-Za-z])([A-Z]{2,3})(?![A-Za-z])", loc):
        if tok in _UPPER_TOKENS:
            found.add(_UPPER_TOKENS[tok])
    if _US_STATE.search(loc) and "canada" not in loc.lower():
        found.add("US")
    if "GB" in found and re.search(r"(?i)new england|cambridge, ma", loc):
        found.discard("GB")
    return found


# ---------------------------------------------------------------- visa signals
# Strong: the posting talks about visas/immigration itself.
POSITIVE = [
    r"visa sponsorship (is )?(available|offered|provided|possible)",
    r"(we|will|can|do|happy to|able to) (also )?sponsor (your |work |employment )?visas?",
    r"sponsor(ship)? (for )?(work )?visas?",
    r"visa (support|assistance|services|help|process support)",
    r"(work permit|immigration) (support|assistance|sponsorship)",
    r"apply from abroad|overseas applicants? (welcome|accepted)|accepts? overseas applica",
    r"visa (is )?possible",
]
# Weak: relocation help, which is often domestic-only (e.g. US benefits lists).
RELOCATION = [
    r"relocation (package|support|assistance|bonus|allowance|budget|stipend|is provided|provided|available)",
    r"(help|support|assist)( you)? (with |to )?relocat",
    r"relocation\? yes",
]
NEGATIVE = [
    r"(not|un)able to (offer |provide )?(visa )?sponsor",
    r"(cannot|can't|can not|won't|will not|do not|don't|does not|doesn't) (offer |provide |currently )*(visa |immigration )?sponsor",
    r"no (visa|immigration) sponsorship",
    r"not (eligible|available) for (visa )?sponsorship",
    r"(visa )?sponsorship is not (available|offered|provided)",
    r"without (the need for |requiring )?(current or future )?(visa |employer )?sponsorship",
    r"must (already )?(have|hold|possess) (the |a |full |valid )?(legal )?(right|authori[sz]ation|eligibility) to work",
    r"(existing|current|valid) right to work",
    r"must be (legally )?(authori[sz]ed|eligible|permitted) to work",
    r"(eu|eea|u\.?s\.?|uk|australian|canadian|swiss) (citizens?(hip)?|nationals?|permanent residents?)( is| are)? (only|required)",
    r"(swedish|danish|norwegian|finnish|german|swiss|dutch|irish|japanese|eu|eea|uk|u\.?s\.?|canadian|australian) "
    r"(work (authori[sz]ation|permit)|residence permit|right to work)[^.]{0,20}(is )?(required|needed|necessary|mandatory)",
    r"(valid|existing|current) (work|residence) permit (is )?(required|needed|mandatory)",
    r"(must|need to|required to) be an? (eu|u\.?s\.?|uk|australian|canadian|swiss) (citizen|national)",
    r"citizenship (is )?required",
    r"(active|current|ability to obtain|obtain and maintain|eligible for) (a |an )?(\w+ )?(security )?clearance",
    r"\b(ts/sci|top secret|nv1|nv2|baseline clearance|sc clearance|dv clearance|sc cleared|dv cleared|bpss)\b",
    r"\b(agsva|negative vetting|security vetting|government vetting)\b",
    r"only (eu|u\.?s\.?|uk|australian|canadian|swiss) (citizens|nationals)",
    r"(eu|european union|u\.?s\.?|australian|canadian|swiss) citizenship",
    r"(japan|uk|eu|us) residents only",
    # GM: "Do not apply for this role if you will need GM immigration sponsorship now or in the future"
    r"(do not|don't|please don't) apply[^.]{0,80}(sponsorship|visa)",
    r"(sponsorship|visa)[^.]{0,40}now or in the future",
    r"(will|would) not (be )?(able to )?(provide|offer|support)[^.]{0,30}(sponsorship|visa)",
    r"(not|un)able to (support|accommodate)[^.]{0,30}(sponsorship|visa)",
    r"(is|are) not (eligible|available) for[^.]{0,20}(sponsorship|visa)",
]
_POS = [re.compile(p, re.I) for p in POSITIVE]
_REL = [re.compile(p, re.I) for p in RELOCATION]
_NEG = [re.compile(p, re.I) for p in NEGATIVE]


def visa_signals(text):
    """Return (visa_snippets, relocation_snippets, negative_snippets)."""
    text = text or ""

    def snippets(patterns):
        out = []
        for rx in patterns:
            m = rx.search(text)
            if m:
                out.append(text[max(0, m.start() - 60): m.end() + 60].replace("\n", " ").strip())
        return out

    def clean(snips):
        # A negative hit also matches the generic "sponsor visas" positive; drop overlaps,
        # and phrases like "relocation support is not provided".
        return [p for p in snips if not any(rx.search(p) for rx in _NEG) and not _POS_VETO.search(p)]

    neg = snippets(_NEG)
    return clean(snippets(_POS)), clean(snippets(_REL)), neg


_POS_VETO = re.compile(
    r"\b(no|not|without|unable to|cannot)\s+(\w+\s+){0,3}(relocat|visa)|relocat\w*\s+(\w+\s+){0,3}not\b", re.I
)


# ----------------------------------------------------------------- visa label
def visa_label(pos, reloc, neg, evidence, policy):
    """One neutral label per posting; the browser turns it into a personal score.

    explicit      the posting offers visa support
    conditional   it offers support with limits (e.g. only for one country)
    blocked       the posting rules sponsorship out
    employer-no   the employer is known not to sponsor
    register      the employer is on that country's sponsor register
    employer-yes  the employer is known to sponsor (config)
    relocation    relocation help only (often domestic)
    unknown       no signal
    """
    if pos and neg:
        return "conditional"
    if pos:
        return "explicit"
    if neg:
        return "blocked"
    if policy == "no":
        return "employer-no"
    if evidence:
        return "register"
    if policy == "yes":
        return "employer-yes"
    if reloc:
        return "relocation"
    return "unknown"
