"""Job-family classification, required skills and required languages.

Families are shared with the web app (knowledge/tracks.json). Tech: security,
software, data, devops, embedded, qa, product. Creative: design, video.
Engineering: mechanical, electrical, civil. Business: marketing, sales,
finance, operations, people. Health: healthcare.
"""

import json
import re
from pathlib import Path

FAMILIES = ("security", "software", "data", "devops", "embedded", "qa", "product", "design", "video",
            "mechanical", "electrical", "civil", "marketing", "sales", "finance", "operations", "people", "healthcare")


def _rx(s):
    return re.compile(s, re.I)


SECURITY = _rx(
    r"\b(security|secops|devsecops|appsec|infosec|cyber\w*|soc\b|siem|detection engineer\w*|incident respon\w*|"
    r"threat|red team|blue team|purple team|penetration|pen ?test\w*|offensive|vulnerabilit\w*|"
    r"grc|governance,? risk|iam\b|identity (and|&) access|cryptograph\w*|forensic\w*|malware|"
    r"reverse engineer\w*|trust (and|&) safety engineer|privacy engineer|fraud engineer|"
    r"product security|cloud security|zero trust|sicherheit\w*|seguran[çc]a)\b")
NOT_SECURITY = _rx(
    r"\b(securities|social security|security (guard|officer|executive|supervisor|personnel|patrol|manpower)|"
    r"physical security|loss prevention|food safety|safety officer|arbeitssicherheit)\b")
PRODUCT = _rx(
    r"\b(product (manager|owner|lead|director|management)|head of product|vp,? product|"
    r"(technical )?program manager|tpm|product operations|gerente de produto)\b")
DESIGN = _rx(
    r"\b(ux|ui|user experience|user interface|product designer|interaction designer|visual designer|"
    r"ux research\w*|user research\w*|design (lead|manager|director)|service designer|content designer|"
    r"graphic designer|graphic design|brand designer|brand design|marketing designer|web designer|"
    r"communication designer|art director|illustrator|grafikdesigner\w*|mediengestalter\w*|"
    r"designer gr[aá]fico|designer)\b")
# Video editing, motion and post-production.
VIDEO = _rx(
    r"\b(video editor|film editor|editor de v[ií]deo|videoeditor\w*|cutter|post[- ]?production|p[oó]s[- ]produ[çc][aã]o|"
    r"motion (designer|graphics|graphic designer|artist)|animator|animador\w*|animation artist|2d artist|3d artist|"
    r"colou?rist|vfx|compositor|videographer|video producer|video production|video content|editor de v[ií]deos|"
    r"video creator|content creator|mediengestalter\w* bild und ton)\b")
# "Designer" titles that aren't graphic, product or UX design.
NOT_DESIGN = _rx(r"\b(hardware|circuit|chip|asic|fpga|pcb|solutions?|instructional|interior|fashion|"
                 r"kitchen|landscape|mechanical|electrical|database|network|learning|curriculum|course|"
                 r"cad|piping|structural|hvac|civil|lighting|tool|mould|mold|packaging)\s+designer")
DATA = _rx(
    r"\b(data (engineer|scientist|analyst|architect|platform|science|engineering|analytics)\w*|analytics engineer|"
    r"machine learning|ml engineer|mlops|ml ops|ai engineer|ai/ml|applied scientist|research scientist|"
    r"deep learning|nlp|computer vision|llm|business intelligence|bi (developer|analyst|engineer)|"
    r"data warehouse|etl|quantitative (analyst|developer|researcher)|cientista de dados|engenheiro de dados|analista de dados)\b")
QA = _rx(
    r"\b(qa|quality assurance|quality engineer|test(ing)? (engineer|automation|analyst|lead|manager)|sdet|"
    r"(software )?(development )?engineer in test|automation tester|tester|testingenieur|analista de testes)\b")
# Quality roles in factories belong to manufacturing, not software testing.
NOT_QA = _rx(r"\b(supplier|manufactur\w*|mechanical|automotive|aerospace|production|plant|welding|casting|"
             r"pharma\w*|gmp|medical device|clinical)\b")
DEVOPS = _rx(
    r"\b(sre|site reliability|devops|platform engineer\w*|infrastructure|infra\b|cloud (engineer|architect)\w*|"
    r"network engineer\w*|systems engineer\w*|system administrator|sysadmin|kubernetes|production engineer\w*|"
    r"reliability|database administrator|dba|release engineer\w*|build engineer\w*|systemadministrator\w*|infraestrutura)\b")
EMBEDDED = _rx(
    r"\b(embedded|firmware|fpga|asic|hardware (design )?engineer\w*|circuit design\w*|ic design\w*|vlsi|electronics?|robotics?|autonomy|autosar|ecu|rtos|"
    r"silicon|verification engineer|pcb|mechatronic\w*|bsp|device driver\w*|embarcad[oa]s?)\b")
SOFTWARE = _rx(
    r"\b(software|developer|programmer|swe|sde|(back|front)[- ]?end|full[- ]?stack|mobile|ios|android|"
    r"web (developer|engineer)|application (developer|engineer)|engineering manager|"
    r"(java|python|golang|go|ruby|rails|node|react|\.net|c\+\+|c#|php|kotlin|swift|scala|rust|typescript) "
    r"(developer|engineer)|game (developer|engineer|programmer)|\w*entwickler\w*|desenvolvedor\w*|programador\w*|"
    r"analista de sistemas|engenheiro de software|(staff|senior|principal|lead|junior) engineer|member of technical staff|engineer)\b")
# Engineers outside software/IT that the catch-all "engineer" would pick up.
NOT_SOFTWARE = _rx(
    r"\b(mechanical|civil|chemical|process|manufacturing|field service|maintenance|structural|hvac|"
    r"construction|sales|solutions?|pre-?sales|customer|support|value|"
    r"electrical installation|facilities|quality control|industrial|environmental|petroleum)\s+engineer")

# ---------------------------------------------------------------- engineering
ELECTRICAL = _rx(
    r"\b(electrical( and electronics?)? (engineer\w*|design\w*|lead|manager)|electrical engineering|"
    r"power (systems?|electronics|distribution|quality) engineer\w*|power electronics|high[- ]voltage|substation|"
    r"protection (and control )?engineer|controls? engineer\w*|control systems engineer|automation engineer|plc|scada|"
    r"instrumentation|i&c|rf engineer|antenna engineer|grid engineer|electrician|"
    r"elektroingenieur\w*|elektrotechnik\w*|elektroniker\w*|elektriker|automatisierungstechnik\w*|sps[- ]programmierer\w*|"
    r"engenheir[oa] el[eé]tric\w*|engenheir[oa] eletricista|engenheir[oa] de automa[çc][aã]o|"
    r"ingeniero el[eé]ctrico|ingeniera el[eé]ctrica|"
    r"elingenj[öo]r\w*|elektroingeni[øo]r\w*|el-?teknisk\w*|elektrotechnisch\w*|s[äa]hk[öo]insin[öo][öo]ri)\b")
# Test-automation and marketing-automation roles aren't controls engineering.
NOT_ELECTRICAL = _rx(r"\b(test automation|marketing automation|qa automation|software|cloud|devops)\b")
# Chip, firmware and software design stay with embedded or software.
NOT_HARD_ENG = _rx(r"\b(software|firmware|embedded|asic|fpga|chip|silicon|analog|digital|rtl|pcb|hardware|circuit|memory|vlsi|cloud|data|ml|ai)\b")
MECHANICAL = _rx(
    r"\b(mechanical (engineer\w*|design\w*|lead|technician)|mechanical engineering|mechanics engineer|"
    r"manufacturing (engineer\w*|technician|manager)|process engineer\w*|industrial engineer\w*|production engineering|"
    r"chemical engineer\w*|materials engineer\w*|aerospace engineer\w*|aeronautical engineer\w*|propulsion engineer\w*|"
    r"structures? engineer|stress engineer|thermal engineer|hvac|piping engineer|tooling engineer|"
    r"design engineer|cad (designer|engineer|technician)|drafts(man|person)|drafter|supplier quality|"
    r"maintenance engineer|field service engineer|automotive engineer|vehicle engineer|powertrain|chassis engineer|"
    r"biomedical engineer|cnc|machinist|mechanic\b|mechaniker\w*|mechatroniker\w*|maschinenbau\w*|konstrukteur\w*|"
    r"verfahrenstechnik\w*|fertigungs\w*|produktionsingenieur\w*|"
    r"maskiningenj[öo]r\w*|maskiningeni[øo]r\w*|maskinkonstrukt[öø]r\w*|konstrukt[öø]r\w*|konstruktionsingeni[øo]r\w*|"
    r"produktionstekniker\w*|maskinmester\w*|werktuigbouw\w*|koneinsin[öo][öo]ri|"
    r"engenheir[oa] mec[aâ]nic[oa]|engenheir[oa] de produ[çc][aã]o|engenheir[oa] de manufatura|engenheir[oa] qu[ií]mic[oa]|"
    r"ingeniero mec[aá]nico|ingeniera mec[aá]nica)\b")
CIVIL = _rx(
    r"\b(civil (engineer\w*|engineering)|structural (engineer\w*|engineering)|geotechnical|geotech engineer|"
    r"transport(ation)? (engineer|planner)|highway engineer|traffic engineer|water (resources )?engineer|"
    r"hydraulic engineer|wastewater|environmental engineer\w*|construction (manager|engineer|project manager|director)|"
    r"site (engineer|manager)|quantity surveyor|cost consultant|building surveyor|building services|mep engineer|"
    r"bim (coordinator|manager|modell?er|engineer|specialist)|architectural (designer|technologist|assistant)|"
    r"landscape architect|urban planner|town planner|bauingenieur\w*|bauleiter\w*|tragwerksplan\w*|statiker\w*|"
    r"engenheir[oa] civil|ingeniero civil|ingeniera civil|arquitet[oa] e urbanista|"
    r"byggnadsingenj[öo]r\w*|bygningsingeni[øo]r\w*|byggingeni[øo]r\w*|bouwkundig\w*|rakennusinsin[öo][öo]ri)\b")

# ------------------------------------------------------------------- business
MARKETING = _rx(
    r"\b(marketing|marketer|marketeer|growth (marketer|manager|lead)|seo|sem\b|ppc|paid (social|search|media)|"
    r"performance market\w*|demand gen\w*|lifecycle market\w*|crm (manager|specialist|lead)|email market\w*|"
    r"content (strategist|marketer|writer|manager|lead|specialist)|copywriter|social media|community manager|"
    r"brand (manager|strategist|lead)|communications (manager|specialist|officer|director|lead|associate|executive)|"
    r"corporate communications|internal communications|public relations|\bpr (manager|specialist|executive)|"
    r"media (buyer|planner)|influencer|pressesprecher\w*|öffentlichkeitsarbeit|"
    r"analista de marketing|comunica[çc][aã]o|redator\w*|marknadsf[öo]r\w*|markedsf[øo]r\w*)\b")
SALES = _rx(
    r"\b(sales|account executive|account manager|account director|key account|business development|"
    r"bdr|sdr|customer success|client success|solutions? (engineer|consultant|architect)|pre-?sales|"
    r"partner (manager|development)|partnerships?|alliances|channel manager|revenue operations|revops|"
    r"inside sales|vertrieb\w*|au[ßs]endienst\w*|kundenberater\w*|vendas|vendedor\w*|executiv[oa] de contas|"
    r"s[äa]ljare|innes[äa]ljare|s[æa]lger\w*|salgs\w*|verkoop\w*|"
    r"executiv[oa] comercial|representante comercial|ventas|comercial\b)\b")
FINANCE = _rx(
    r"\b(accountant|accounting|accounts (payable|receivable)|bookkeep\w*|auditor|audit|controller|controlling|"
    r"fp&a|financial (analyst|planning|controller|reporting|accountant|manager)|finance (manager|director|analyst|"
    r"associate|business partner|lead|operations)|head of finance|vp,? finance|cfo|chief financial officer|treasury|"
    r"tax (manager|analyst|advisor|adviser|accountant|specialist|associate|director)|payroll|actuar\w*|"
    r"credit (analyst|risk)|risk (analyst|manager)|investment (analyst|associate|banking)|equity research|"
    r"portfolio manager|securities|underwriter|compliance (analyst|officer|manager)|"
    r"buchhalt\w*|bilanzbuchhalt\w*|finanzbuchhalt\w*|steuerfach\w*|steuerberater\w*|wirtschaftspr[üu]f\w*|"
    r"contador\w*|contabilidade|analista financeiro|analista cont[aá]bil|controladoria|auditor\w*|"
    r"redovisning\w*|ekonomiassistent\w*|ekonomichef\w*|bogholder\w*|regnskab\w*|revisor\w*|"
    r"[øo]konomimedarbejder\w*|kreditormedarbejder|debitormedarbejder|boekhoud\w*|kirjanpit[äa]j[äa])\b")
# A tech word in the title makes it a tech role ("Marketing Data Engineer").
NOT_BUSINESS = _rx(r"\b(engineers?|developers?|programmers?|scientists?|software|cyber\w*|security|it risk)\b")
OPERATIONS = _rx(
    r"\b(supply chain|logistics?|procurement|purchasing|buyer|sourcing (manager|specialist|lead|analyst)|"
    r"category manager|demand planner|supply planner|production planner|inventory|warehouse (manager|supervisor|lead)|"
    r"fulfil?ment|operations (manager|analyst|lead|director|specialist|associate|coordinator|executive)|"
    r"head of operations|business operations|chief operating officer|coo\b|project (manager|coordinator|lead|director)|"
    r"programme manager|pmo|business analyst|process improvement|continuous improvement|lean|six sigma|"
    r"operational excellence|einkauf\w*|eink[äa]ufer\w*|logistik\w*|disponent\w*|projektleit\w*|projektmanag\w*|"
    r"comprador\w*|suprimentos|log[ií]stica|gerente de projetos?|analista de neg[oó]cios|"
    r"projektledare\w*|projektleder\w*|prosjektleder\w*|projectleider\w*|projektkoordinator\w*|"
    r"ink[öo]pare\w*|indk[øo]ber\w*|logistiker\w*)\b")
PEOPLE = _rx(
    r"\b(recruit\w*|talent (acquisition|partner|sourcer|manager|lead|advisor)|sourcer|"
    r"hr (business partner|manager|generalist|director|coordinator|specialist|advisor|adviser|analyst|lead|operations)|"
    r"hrbp|human resources|people (partner|operations|ops|business partner|manager|team|experience|analytics|lead|director)|"
    r"head of people|chief people officer|compensation|total rewards|benefits (manager|specialist|analyst)|"
    r"learning (and|&) development|l&d|hris|personalreferent\w*|personalsachbearbeit\w*|personalentwickl\w*|"
    r"recrutador\w*|recrutamento|analista de rh|recursos humanos|business partner de rh|"
    r"rekryter\w*|rekruttering\w*|rekrutterer\w*|hr-(specialist|generalist|partner|chef|konsulent|ansvarig)\w*)\b")

# ------------------------------------------------------------------- health
HEALTHCARE = _rx(
    r"\b(nurse|nursing|registered nurse|rn\b|midwife|midwives|physician|doctor|medical officer|general practitioner|"
    r"gp\b|surgeon|anaesthet\w*|anesthesi\w*|psychiatrist|radiologist|paediatrician|pediatrician|cardiologist|"
    r"oncologist|dentist|dental (nurse|hygienist|therapist)|pharmacist|pharmacy technician|physiotherapist|"
    r"physical therapist|occupational therapist|speech (and language )?therapist|dietitian|radiographer|sonographer|"
    r"paramedic|biomedical scientist|medical laboratory|clinical scientist|clinical psychologist|optometrist|"
    r"care (worker|assistant)|healthcare assistant|support worker|carer|caregiver|veterinar\w*|"
    r"pflegefach\w*|krankenpfleg\w*|gesundheits- und krankenpfleg\w*|altenpfleg\w*|pflegekraft|pflegekr[äa]fte|"
    r"hebamme|arzt|zahnarzt\w*|tierarzt\w*|[äa]rztin|assistenzarzt\w*|facharzt\w*|physiotherapeut\w*|apotheker\w*|"
    r"enfermeir[oa]|t[eé]cnic[oa] de enfermagem|m[eé]dic[oa]|fisioterapeuta|farmac[eê]utic[oa]|"
    r"enfermer[oa]|sjuksk[öo]terska|l[äa]kare|sygeplejerske|sykepleier|verpleegkundige|sairaanhoitaja|l[äa][äa]k[äa]ri|"
    r"undersk[öo]terska|tandl[äa]kare|fysioterapeut\w*|sosu-\w+|sundhedsplejersk\w*|\blege\b)\b")
NOT_HEALTH = _rx(r"\b(sales|marketing|recruit\w*|software|engineer\w*|developer|data|product|account)\b")

# Roles outside every family (legal, policy, admin).
NON_TECH = _rx(
    r"\b(counsel|legal|lawyer|paralegal|attorney|public policy|policy (lead|manager)|executive assistant|"
    r"office manager|receptionist|chef|cook)\b")

_ORDER = [
    ("product", PRODUCT, None),
    ("people", PEOPLE, None),
    ("sales", SALES, None),
    ("marketing", MARKETING, NOT_BUSINESS),
    ("finance", FINANCE, NOT_BUSINESS),
    ("healthcare", HEALTHCARE, NOT_HEALTH),
    ("security", SECURITY, NOT_SECURITY),
    ("data", DATA, None),
    ("qa", QA, NOT_QA),
    ("devops", DEVOPS, None),
    ("electrical", ELECTRICAL, NOT_ELECTRICAL),
    ("mechanical", MECHANICAL, NOT_HARD_ENG),
    ("civil", CIVIL, NOT_HARD_ENG),
    ("embedded", EMBEDDED, None),
    ("operations", OPERATIONS, None),
    ("software", SOFTWARE, NOT_SOFTWARE),
]

# Creative roles often sit in marketing or communications teams ("Video Editor,
# Marketing"), so they are matched first.
_CREATIVE = [("video", VIDEO, None), ("design", DESIGN, NOT_DESIGN)]
NOT_CREATIVE = _rx(r"\b(recruit\w*|sales|account (executive|manager)|talent|customer success)\b")


def job_family(title):
    """The job family of a posting title, or None when it fits none of them."""
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
