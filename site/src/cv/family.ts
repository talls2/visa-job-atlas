// Job-family classification. GENERATED from pipeline/jobtracker/families.py
// by pipeline/gen_family_ts.py; edit the Python file and regenerate.
import type { Family } from "../types";

const rx = (s: string) => new RegExp(s, "i");

const VIDEO = rx("\\b(video editor|film editor|editor de v[ií]deo|videoeditor\\w*|cutter|post[- ]?production|p[oó]s[- ]produ[çc][aã]o|motion (designer|graphics|graphic designer|artist)|animator|animador\\w*|animation artist|2d artist|3d artist|colou?rist|vfx|compositor|videographer|video producer|video production|video content|editor de v[ií]deos|video creator|content creator|mediengestalter\\w* bild und ton)\\b");
const DESIGN = rx("\\b(ux|ui|user experience|user interface|product designer|interaction designer|visual designer|ux research\\w*|user research\\w*|design (lead|manager|director)|service designer|content designer|graphic designer|graphic design|brand designer|brand design|marketing designer|web designer|communication designer|art director|illustrator|grafikdesigner\\w*|mediengestalter\\w*|designer gr[aá]fico|designer)\\b");
const NOT_DESIGN = rx("\\b(hardware|circuit|chip|asic|fpga|pcb|solutions?|instructional|interior|fashion|kitchen|landscape|mechanical|electrical|database|network|learning|curriculum|course|cad|piping|structural|hvac|civil|lighting|tool|mould|mold|packaging)\\s+designer");
const PRODUCT = rx("\\b(product (manager|owner|lead|director|management)|head of product|vp,? product|(technical )?program manager|tpm|product operations|gerente de produto)\\b");
const PEOPLE = rx("\\b(recruit\\w*|talent (acquisition|partner|sourcer|manager|lead|advisor)|sourcer|hr (business partner|manager|generalist|director|coordinator|specialist|advisor|adviser|analyst|lead|operations)|hrbp|human resources|people (partner|operations|ops|business partner|manager|team|experience|analytics|lead|director)|head of people|chief people officer|compensation|total rewards|benefits (manager|specialist|analyst)|learning (and|&) development|l&d|hris|personalreferent\\w*|personalsachbearbeit\\w*|personalentwickl\\w*|recrutador\\w*|recrutamento|analista de rh|recursos humanos|business partner de rh|rekryter\\w*|rekruttering\\w*|rekrutterer\\w*|hr-(specialist|generalist|partner|chef|konsulent|ansvarig)\\w*)\\b");
const SALES = rx("\\b(sales|account executive|account manager|account director|key account|business development|bdr|sdr|customer success|client success|solutions? (engineer|consultant|architect)|pre-?sales|partner (manager|development)|partnerships?|alliances|channel manager|revenue operations|revops|inside sales|vertrieb\\w*|au[ßs]endienst\\w*|kundenberater\\w*|vendas|vendedor\\w*|executiv[oa] de contas|s[äa]ljare|innes[äa]ljare|s[æa]lger\\w*|salgs\\w*|verkoop\\w*|executiv[oa] comercial|representante comercial|ventas|comercial\\b)\\b");
const MARKETING = rx("\\b(marketing|marketer|marketeer|growth (marketer|manager|lead)|seo|sem\\b|ppc|paid (social|search|media)|performance market\\w*|demand gen\\w*|lifecycle market\\w*|crm (manager|specialist|lead)|email market\\w*|content (strategist|marketer|writer|manager|lead|specialist)|copywriter|social media|community manager|brand (manager|strategist|lead)|communications (manager|specialist|officer|director|lead|associate|executive)|corporate communications|internal communications|public relations|\\bpr (manager|specialist|executive)|media (buyer|planner)|influencer|pressesprecher\\w*|öffentlichkeitsarbeit|analista de marketing|comunica[çc][aã]o|redator\\w*|marknadsf[öo]r\\w*|markedsf[øo]r\\w*)\\b");
const NOT_BUSINESS = rx("\\b(engineers?|developers?|programmers?|scientists?|software|cyber\\w*|security|it risk)\\b");
const FINANCE = rx("\\b(accountant|accounting|accounts (payable|receivable)|bookkeep\\w*|auditor|audit|controller|controlling|fp&a|financial (analyst|planning|controller|reporting|accountant|manager)|finance (manager|director|analyst|associate|business partner|lead|operations)|head of finance|vp,? finance|cfo|chief financial officer|treasury|tax (manager|analyst|advisor|adviser|accountant|specialist|associate|director)|payroll|actuar\\w*|credit (analyst|risk)|risk (analyst|manager)|investment (analyst|associate|banking)|equity research|portfolio manager|securities|underwriter|compliance (analyst|officer|manager)|buchhalt\\w*|bilanzbuchhalt\\w*|finanzbuchhalt\\w*|steuerfach\\w*|steuerberater\\w*|wirtschaftspr[üu]f\\w*|contador\\w*|contabilidade|analista financeiro|analista cont[aá]bil|controladoria|auditor\\w*|redovisning\\w*|ekonomiassistent\\w*|ekonomichef\\w*|bogholder\\w*|regnskab\\w*|revisor\\w*|[øo]konomimedarbejder\\w*|kreditormedarbejder|debitormedarbejder|boekhoud\\w*|kirjanpit[äa]j[äa])\\b");
const HEALTHCARE = rx("\\b(nurse|nursing|registered nurse|rn\\b|midwife|midwives|physician|doctor|medical officer|general practitioner|gp\\b|surgeon|anaesthet\\w*|anesthesi\\w*|psychiatrist|radiologist|paediatrician|pediatrician|cardiologist|oncologist|dentist|dental (nurse|hygienist|therapist)|pharmacist|pharmacy technician|physiotherapist|physical therapist|occupational therapist|speech (and language )?therapist|dietitian|radiographer|sonographer|paramedic|biomedical scientist|medical laboratory|clinical scientist|clinical psychologist|optometrist|care (worker|assistant)|healthcare assistant|support worker|carer|caregiver|veterinar\\w*|pflegefach\\w*|krankenpfleg\\w*|gesundheits- und krankenpfleg\\w*|altenpfleg\\w*|pflegekraft|pflegekr[äa]fte|hebamme|arzt|zahnarzt\\w*|tierarzt\\w*|[äa]rztin|assistenzarzt\\w*|facharzt\\w*|physiotherapeut\\w*|apotheker\\w*|enfermeir[oa]|t[eé]cnic[oa] de enfermagem|m[eé]dic[oa]|fisioterapeuta|farmac[eê]utic[oa]|enfermer[oa]|sjuksk[öo]terska|l[äa]kare|sygeplejerske|sykepleier|verpleegkundige|sairaanhoitaja|l[äa][äa]k[äa]ri|undersk[öo]terska|tandl[äa]kare|fysioterapeut\\w*|sosu-\\w+|sundhedsplejersk\\w*|\\blege\\b)\\b");
const NOT_HEALTH = rx("\\b(sales|marketing|recruit\\w*|software|engineer\\w*|developer|data|product|account)\\b");
const SECURITY = rx("\\b(security|secops|devsecops|appsec|infosec|cyber\\w*|soc\\b|siem|detection engineer\\w*|incident respon\\w*|threat|red team|blue team|purple team|penetration|pen ?test\\w*|offensive|vulnerabilit\\w*|grc|governance,? risk|iam\\b|identity (and|&) access|cryptograph\\w*|forensic\\w*|malware|reverse engineer\\w*|trust (and|&) safety engineer|privacy engineer|fraud engineer|product security|cloud security|zero trust|sicherheit\\w*|seguran[çc]a)\\b");
const NOT_SECURITY = rx("\\b(securities|social security|security (guard|officer|executive|supervisor|personnel|patrol|manpower)|physical security|loss prevention|food safety|safety officer|arbeitssicherheit)\\b");
const DATA = rx("\\b(data (engineer|scientist|analyst|architect|platform|science|engineering|analytics)\\w*|analytics engineer|machine learning|ml engineer|mlops|ml ops|ai engineer|ai/ml|applied scientist|research scientist|deep learning|nlp|computer vision|llm|business intelligence|bi (developer|analyst|engineer)|data warehouse|etl|quantitative (analyst|developer|researcher)|cientista de dados|engenheiro de dados|analista de dados)\\b");
const QA = rx("\\b(qa|quality assurance|quality engineer|test(ing)? (engineer|automation|analyst|lead|manager)|sdet|(software )?(development )?engineer in test|automation tester|tester|testingenieur|analista de testes)\\b");
const NOT_QA = rx("\\b(supplier|manufactur\\w*|mechanical|automotive|aerospace|production|plant|welding|casting|pharma\\w*|gmp|medical device|clinical)\\b");
const DEVOPS = rx("\\b(sre|site reliability|devops|platform engineer\\w*|infrastructure|infra\\b|cloud (engineer|architect)\\w*|network engineer\\w*|systems engineer\\w*|system administrator|sysadmin|kubernetes|production engineer\\w*|reliability|database administrator|dba|release engineer\\w*|build engineer\\w*|systemadministrator\\w*|infraestrutura)\\b");
const ELECTRICAL = rx("\\b(electrical( and electronics?)? (engineer\\w*|design\\w*|lead|manager)|electrical engineering|power (systems?|electronics|distribution|quality) engineer\\w*|power electronics|high[- ]voltage|substation|protection (and control )?engineer|controls? engineer\\w*|control systems engineer|automation engineer|plc|scada|instrumentation|i&c|rf engineer|antenna engineer|grid engineer|electrician|elektroingenieur\\w*|elektrotechnik\\w*|elektroniker\\w*|elektriker|automatisierungstechnik\\w*|sps[- ]programmierer\\w*|engenheir[oa] el[eé]tric\\w*|engenheir[oa] eletricista|engenheir[oa] de automa[çc][aã]o|ingeniero el[eé]ctrico|ingeniera el[eé]ctrica|elingenj[öo]r\\w*|elektroingeni[øo]r\\w*|el-?teknisk\\w*|elektrotechnisch\\w*|s[äa]hk[öo]insin[öo][öo]ri)\\b");
const NOT_ELECTRICAL = rx("\\b(test automation|marketing automation|qa automation|software|cloud|devops)\\b");
const MECHANICAL = rx("\\b(mechanical (engineer\\w*|design\\w*|lead|technician)|mechanical engineering|mechanics engineer|manufacturing (engineer\\w*|technician|manager)|process engineer\\w*|industrial engineer\\w*|production engineering|chemical engineer\\w*|materials engineer\\w*|aerospace engineer\\w*|aeronautical engineer\\w*|propulsion engineer\\w*|structures? engineer|stress engineer|thermal engineer|hvac|piping engineer|tooling engineer|design engineer|cad (designer|engineer|technician)|drafts(man|person)|drafter|supplier quality|maintenance engineer|field service engineer|automotive engineer|vehicle engineer|powertrain|chassis engineer|biomedical engineer|cnc|machinist|mechanic\\b|mechaniker\\w*|mechatroniker\\w*|maschinenbau\\w*|konstrukteur\\w*|verfahrenstechnik\\w*|fertigungs\\w*|produktionsingenieur\\w*|maskiningenj[öo]r\\w*|maskiningeni[øo]r\\w*|maskinkonstrukt[öø]r\\w*|konstrukt[öø]r\\w*|konstruktionsingeni[øo]r\\w*|produktionstekniker\\w*|maskinmester\\w*|werktuigbouw\\w*|koneinsin[öo][öo]ri|engenheir[oa] mec[aâ]nic[oa]|engenheir[oa] de produ[çc][aã]o|engenheir[oa] de manufatura|engenheir[oa] qu[ií]mic[oa]|ingeniero mec[aá]nico|ingeniera mec[aá]nica)\\b");
const NOT_HARD_ENG = rx("\\b(software|firmware|embedded|asic|fpga|chip|silicon|analog|digital|rtl|pcb|hardware|circuit|memory|vlsi|cloud|data|ml|ai)\\b");
const CIVIL = rx("\\b(civil (engineer\\w*|engineering)|structural (engineer\\w*|engineering)|geotechnical|geotech engineer|transport(ation)? (engineer|planner)|highway engineer|traffic engineer|water (resources )?engineer|hydraulic engineer|wastewater|environmental engineer\\w*|construction (manager|engineer|project manager|director)|site (engineer|manager)|quantity surveyor|cost consultant|building surveyor|building services|mep engineer|bim (coordinator|manager|modell?er|engineer|specialist)|architectural (designer|technologist|assistant)|landscape architect|urban planner|town planner|bauingenieur\\w*|bauleiter\\w*|tragwerksplan\\w*|statiker\\w*|engenheir[oa] civil|ingeniero civil|ingeniera civil|arquitet[oa] e urbanista|byggnadsingenj[öo]r\\w*|bygningsingeni[øo]r\\w*|byggingeni[øo]r\\w*|bouwkundig\\w*|rakennusinsin[öo][öo]ri)\\b");
const EMBEDDED = rx("\\b(embedded|firmware|fpga|asic|hardware (design )?engineer\\w*|circuit design\\w*|ic design\\w*|vlsi|electronics?|robotics?|autonomy|autosar|ecu|rtos|silicon|verification engineer|pcb|mechatronic\\w*|bsp|device driver\\w*|embarcad[oa]s?)\\b");
const OPERATIONS = rx("\\b(supply chain|logistics?|procurement|purchasing|buyer|sourcing (manager|specialist|lead|analyst)|category manager|demand planner|supply planner|production planner|inventory|warehouse (manager|supervisor|lead)|fulfil?ment|operations (manager|analyst|lead|director|specialist|associate|coordinator|executive)|head of operations|business operations|chief operating officer|coo\\b|project (manager|coordinator|lead|director)|programme manager|pmo|business analyst|process improvement|continuous improvement|lean|six sigma|operational excellence|einkauf\\w*|eink[äa]ufer\\w*|logistik\\w*|disponent\\w*|projektleit\\w*|projektmanag\\w*|comprador\\w*|suprimentos|log[ií]stica|gerente de projetos?|analista de neg[oó]cios|projektledare\\w*|projektleder\\w*|prosjektleder\\w*|projectleider\\w*|projektkoordinator\\w*|ink[öo]pare\\w*|indk[øo]ber\\w*|logistiker\\w*)\\b");
const SOFTWARE = rx("\\b(software|developer|programmer|swe|sde|(back|front)[- ]?end|full[- ]?stack|mobile|ios|android|web (developer|engineer)|application (developer|engineer)|engineering manager|(java|python|golang|go|ruby|rails|node|react|\\.net|c\\+\\+|c#|php|kotlin|swift|scala|rust|typescript) (developer|engineer)|game (developer|engineer|programmer)|\\w*entwickler\\w*|desenvolvedor\\w*|programador\\w*|analista de sistemas|engenheiro de software|(staff|senior|principal|lead|junior) engineer|member of technical staff|engineer)\\b");
const NOT_SOFTWARE = rx("\\b(mechanical|civil|chemical|process|manufacturing|field service|maintenance|structural|hvac|construction|sales|solutions?|pre-?sales|customer|support|value|electrical installation|facilities|quality control|industrial|environmental|petroleum)\\s+engineer");
const NOT_CREATIVE = rx("\\b(recruit\\w*|sales|account (executive|manager)|talent|customer success)\\b");
const NON_TECH = rx("\\b(counsel|legal|lawyer|paralegal|attorney|public policy|policy (lead|manager)|executive assistant|office manager|receptionist|chef|cook)\\b");

const ORDER: [Family, RegExp, RegExp | null][] = [
  ["product", PRODUCT, null],
  ["people", PEOPLE, null],
  ["sales", SALES, null],
  ["marketing", MARKETING, NOT_BUSINESS],
  ["finance", FINANCE, NOT_BUSINESS],
  ["healthcare", HEALTHCARE, NOT_HEALTH],
  ["security", SECURITY, NOT_SECURITY],
  ["data", DATA, null],
  ["qa", QA, NOT_QA],
  ["devops", DEVOPS, null],
  ["electrical", ELECTRICAL, NOT_ELECTRICAL],
  ["mechanical", MECHANICAL, NOT_HARD_ENG],
  ["civil", CIVIL, NOT_HARD_ENG],
  ["embedded", EMBEDDED, null],
  ["operations", OPERATIONS, null],
  ["software", SOFTWARE, NOT_SOFTWARE],
];

// Creative roles often sit in marketing teams ("Video Editor, Marketing"), so they
// are matched first.
const CREATIVE: [Family, RegExp, RegExp | null][] = [
  ["video", VIDEO, null],
  ["design", DESIGN, NOT_DESIGN],
];

export function jobFamily(title: string): Family | null {
  if (!title) return null;
  if (!NOT_CREATIVE.test(title)) {
    for (const [family, re, veto] of CREATIVE) {
      if (re.test(title) && !(veto && veto.test(title))) return family;
    }
  }
  if (NON_TECH.test(title)) return null;
  for (const [family, re, veto] of ORDER) {
    if (re.test(title) && !(veto && veto.test(title))) return family;
  }
  return null;
}
