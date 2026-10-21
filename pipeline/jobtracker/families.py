"""Job-family classification, required skills and required languages.

Families are shared with the web app (knowledge/tracks.json):
security, software, data, devops, embedded, qa, product, design.
"""

import json
import re
from pathlib import Path

FAMILIES = ("security", "software", "data", "devops", "embedded", "qa", "product", "design", "video")

SECURITY = re.compile(
    r"\b(security|secops|devsecops|appsec|infosec|cyber\w*|soc\b|siem|detection engineer\w*|incident respon\w*|"
    r"threat|red team|blue team|purple team|penetration|pen ?test\w*|offensive|vulnerabilit\w*|"
    r"grc|governance,? risk|iam\b|identity (and|&) access|cryptograph\w*|forensic\w*|malware|"
    r"reverse engineer\w*|trust (and|&) safety engineer|privacy engineer|fraud engineer|"
    r"product security|cloud security|zero trust|sicherheit\w*)\b",
    re.I,
)
NOT_SECURITY = re.compile(
    r"\b(securities|social security|security (guard|officer|executive|supervisor|personnel|patrol|manpower)|"
    r"physical security|loss prevention|food safety|safety officer|arbeitssicherheit)\b",
    re.I,
)
PRODUCT = re.compile(
    r"\b(product (manager|owner|lead|director|management)|head of product|vp,? product|"
    r"(technical )?program manager|tpm|product operations)\b", re.I)
DESIGN = re.compile(
    r"\b(ux|ui|user experience|user interface|product designer|interaction designer|visual designer|"
    r"ux research\w*|user research\w*|design (lead|manager|director)|service designer|content designer|"
    r"graphic designer|graphic design|brand designer|brand design|marketing designer|web designer|"
    r"communication designer|art director|illustrator|grafikdesigner\w*|mediengestalter\w*|"
    r"designer gr[aá]fico|designer)\b", re.I)
# Video editing, motion and post-production.
VIDEO = re.compile(
    r"\b(video editor|film editor|editor de v[ií]deo|videoeditor\w*|cutter|post[- ]?production|"
    r"motion (designer|graphics|graphic designer|artist)|animator|animation artist|2d artist|3d artist|"
    r"colou?rist|vfx|compositor|videographer|video producer|video production|video content|"
    r"video creator|content creator|mediengestalter\w* bild und ton)\b", re.I)
# "Designer" titles that aren't graphic, product or UX design.
NOT_DESIGN = re.compile(r"\b(hardware|circuit|chip|asic|fpga|pcb|solutions?|instructional|interior|fashion|"
                        r"kitchen|landscape|mechanical|electrical|database|network|learning|curriculum|course)\s+designer", re.I)
DATA = re.compile(
    r"\b(data (engineer|scientist|analyst|architect|platform|science|engineering|analytics)\w*|analytics engineer|"
    r"machine learning|ml engineer|mlops|ml ops|ai engineer|ai/ml|applied scientist|research scientist|"
    r"deep learning|nlp|computer vision|llm|business intelligence|bi (developer|analyst|engineer)|"
    r"data warehouse|etl|quantitative (analyst|developer|researcher))\b", re.I)
QA = re.compile(
    r"\b(qa|quality assurance|quality engineer|test(ing)? (engineer|automation|analyst|lead|manager)|sdet|"
    r"(software )?(development )?engineer in test|automation tester|tester|testingenieur)\b", re.I)
DEVOPS = re.compile(
    r"\b(sre|site reliability|devops|platform engineer\w*|infrastructure|infra\b|cloud (engineer|architect)\w*|"
    r"network engineer\w*|systems engineer\w*|system administrator|sysadmin|kubernetes|production engineer\w*|"
    r"reliability|database administrator|dba|release engineer\w*|build engineer\w*|systemadministrator\w*)\b", re.I)
EMBEDDED = re.compile(
    r"\b(embedded|firmware|fpga|asic|hardware engineer\w*|electronics?|robotics?|autonomy|autosar|ecu|rtos|"
    r"silicon|verification engineer|pcb|mechatronic\w*|bsp|device driver\w*)\b", re.I)
SOFTWARE = re.compile(
    r"\b(software|developer|programmer|swe|sde|(back|front)[- ]?end|full[- ]?stack|mobile|ios|android|"
    r"web (developer|engineer)|application (developer|engineer)|engineering manager|"
    r"(java|python|golang|go|ruby|rails|node|react|\.net|c\+\+|c#|php|kotlin|swift|scala|rust|typescript) "
    r"(developer|engineer)|game (developer|engineer|programmer)|\w*entwickler\w*|desenvolvedor\w*|"
    r"(staff|senior|principal|lead|junior) engineer|member of technical staff|engineer)\b", re.I)
# Engineers outside software/IT that the catch-all "engineer" would pick up.
NOT_SOFTWARE = re.compile(
    r"\b(mechanical|civil|chemical|process|manufacturing|field service|maintenance|structural|hvac|"
    r"construction|sales|solutions?|pre-?sales|customer|support|value|"
    r"electrical installation|facilities|quality control|industrial|environmental|petroleum)\s+engineer", re.I)

# Non-engineering roles that merely mention a tech word ("Security Sales Specialist").
NON_TECH = re.compile(
    r"\b(sales|account executive|account manager|marketing|partner manager|partnerships?|alliances|"
    r"counsel|legal|lawyer|paralegal|recruit\w*|talent|customer success|client value|business development|"
    r"bdr|sdr|go[- ]to[- ]market|gtm|communications|public policy|policy (lead|manager)|executive assistant|"
    r"accountant|payroll|office manager|copywriter)\b",
    re.I,
)

_ORDER = [("product", PRODUCT, None), ("video", VIDEO, None), ("design", DESIGN, NOT_DESIGN), ("security", SECURITY, NOT_SECURITY),
          ("data", DATA, None), ("qa", QA, None), ("devops", DEVOPS, None), ("embedded", EMBEDDED, None),
          ("software", SOFTWARE, NOT_SOFTWARE)]


# Creative roles often sit in marketing or communications teams ("Video Editor,
# Marketing"), so they are matched before the non-tech filter.
_CREATIVE = [("video", VIDEO, None), ("design", DESIGN, NOT_DESIGN)]
NOT_CREATIVE = re.compile(r"\b(recruit\w*|sales|account (executive|manager)|talent|customer success)\b", re.I)


def job_family(title):
    """The job family of a posting title, or None when it isn't a tech or creative role."""
    if not title:
        return None
    if not NOT_CREATIVE.search(title):
        for family, rx, veto in _CREATIVE:
            if rx.search(title) and not (veto and veto.search(title)):
                return family
    if NON_TECH.search(title):
        return None
    for family, rx, veto in _ORDER:
        if rx.search(title) and not (veto and veto.search(title)):
            return family
    return None


# --------------------------------------------------------------------- skills
SKILLS_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "skills.json"
_SKILLS = None


def _skill_rx():
    global _SKILLS
    if _SKILLS is None:
        data = json.loads(SKILLS_PATH.read_text(encoding="utf-8"))
        _SKILLS = [(s["id"], re.compile(r"(?<![\w+#.])(" + "|".join(s["patterns"]) + r")(?![\w+#])", re.I))
                   for s in data["skills"]]
    return _SKILLS


def skills(text, limit=12):
    """Skill ids found in a posting, most-mentioned first."""
    counts = []
    for sid, rx in _skill_rx():
        n = len(rx.findall(text or ""))
        if n:
            counts.append((n, sid))
    counts.sort(key=lambda c: (-c[0], c[1]))
    return [sid for _, sid in counts[:limit]]


# ------------------------------------------------------------------ languages
# Non-English languages a posting requires: asked for explicitly, or the posting
# itself is written in that language.
_LANG_NAMES = {
    "de": r"german|deutsch\w*", "ja": r"japanese|nihongo|日本語", "fr": r"french|français|francais",
    "nl": r"dutch|nederlands", "sv": r"swedish|svenska", "da": r"danish|dansk", "no": r"norwegian|norsk",
    "fi": r"finnish|suomi", "es": r"spanish|español|espanol|castellano", "pt": r"portuguese|português",
    "it": r"italian|italiano", "ko": r"korean|한국어", "zh": r"mandarin|chinese|中文", "pl": r"polish|polski",
}
_NEED = re.compile(r"fluent|fluency|native|proficien\w*|business[- ]level|business|required|must|mandatory|"
                   r"essential|\bc1\b|\bc2\b|\bb2\b|\bn1\b|\bn2\b|jlpt|kenntnisse|fließend|fliessend|"
                   r"verhandlungssicher|sehr gute?|excellent|strong|good command|written and spoken", re.I)
_NICE = re.compile(r"nice[- ]to[- ]have|a plus|is a plus|bonus|preferred|advantage\w*|desirable|beneficial|"
                   r"von vorteil|wünschenswert|optional|not required|no .{0,15}required", re.I)
_LANG_RX = {code: re.compile(r"(?<!\w)(" + names + r")(?!\w)", re.I) for code, names in _LANG_NAMES.items()}
_STOPWORDS = {
    "de": {"und", "die", "der", "mit", "für", "wir", "sie", "ist", "eine", "ihre", "bei", "auf"},
    "nl": {"en", "het", "een", "van", "wij", "jij", "voor", "met", "zijn", "bij"},
    "sv": {"och", "att", "för", "med", "som", "är", "vi", "du", "på", "har"},
    "da": {"og", "at", "for", "med", "som", "er", "vi", "du", "på", "har", "til"},
    "fr": {"et", "les", "des", "pour", "avec", "nous", "vous", "une", "dans", "est"},
    "es": {"y", "los", "las", "para", "con", "nuestro", "una", "del", "en", "es"},
}
_WORD = re.compile(r"[a-zäöüßåæøéèàçñ]+", re.I)
_KANA = re.compile(r"[぀-ヿ]")


def required_languages(text):
    """Sorted ISO 639-1 codes of non-English languages the posting requires."""
    text = text or ""
    found = set()
    for code, rx in _LANG_RX.items():
        for m in rx.finditer(text):
            window = text[max(0, m.start() - 80): m.end() + 80]
            if _NEED.search(window) and not _NICE.search(window):
                found.add(code)
                break
    if len(_KANA.findall(text[:3000])) > 40:
        found.add("ja")
    words = [w.lower() for w in _WORD.findall(text[:4000])]
    if len(words) > 60:
        for code, stop in _STOPWORDS.items():
            if sum(w in stop for w in words) / len(words) > 0.12:
                found.add(code)
    found.discard("en")
    return sorted(found)
