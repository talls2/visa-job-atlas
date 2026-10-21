// Job-family classification, mirrored from pipeline/jobtracker/families.py.
import type { Family } from "../types";

const rx = (s: string) => new RegExp(s, "i");

const SECURITY = rx(
  "\\b(security|secops|devsecops|appsec|infosec|cyber\\w*|soc\\b|siem|detection engineer\\w*|incident respon\\w*|" +
    "threat|red team|blue team|purple team|penetration|pen ?test\\w*|offensive|vulnerabilit\\w*|" +
    "grc|governance,? risk|iam\\b|identity (and|&) access|cryptograph\\w*|forensic\\w*|malware|" +
    "reverse engineer\\w*|trust (and|&) safety engineer|privacy engineer|fraud engineer|" +
    "product security|cloud security|zero trust|sicherheit\\w*|seguran[çc]a)\\b",
);
const NOT_SECURITY = rx(
  "\\b(securities|social security|security (guard|officer|executive|supervisor|personnel|patrol|manpower)|" +
    "physical security|loss prevention|food safety|safety officer|arbeitssicherheit)\\b",
);
const PRODUCT = rx(
  "\\b(product (manager|owner|lead|director|management)|head of product|vp,? product|" +
    "(technical )?program manager|tpm|product operations|gerente de produto)\\b",
);
const DESIGN = rx(
  "\\b(ux|ui|user experience|user interface|product designer|interaction designer|visual designer|" +
    "ux research\\w*|user research\\w*|design (lead|manager|director)|service designer|content designer|" +
    "graphic designer|graphic design|brand designer|brand design|marketing designer|web designer|" +
    "communication designer|art director|illustrator|grafikdesigner\\w*|mediengestalter\\w*|" +
    "designer gr[aá]fico|designer)\\b",
);
// Video editing, motion and post-production.
const VIDEO = rx(
  "\\b(video editor|film editor|editor de v[ií]deo|videoeditor\\w*|cutter|post[- ]?production|p[oó]s[- ]produ[çc][aã]o|" +
    "motion (designer|graphics|graphic designer|artist)|animator|animador\\w*|animation artist|2d artist|3d artist|" +
    "colou?rist|vfx|compositor|videographer|video producer|video production|video content|editor de v[ií]deos|" +
    "video creator|content creator|mediengestalter\\w* bild und ton)\\b",
);
const NOT_DESIGN = rx(
  "\\b(hardware|circuit|chip|asic|fpga|pcb|solutions?|instructional|interior|fashion|" +
    "kitchen|landscape|mechanical|electrical|database|network|learning|curriculum|course)\\s+designer",
);
const NOT_CREATIVE = rx("\\b(recruit\\w*|sales|account (executive|manager)|talent|customer success)\\b");
const DATA = rx(
  "\\b(data (engineer|scientist|analyst|architect|platform|science|engineering|analytics)\\w*|analytics engineer|" +
    "machine learning|ml engineer|mlops|ml ops|ai engineer|ai/ml|applied scientist|research scientist|" +
    "deep learning|nlp|computer vision|llm|business intelligence|bi (developer|analyst|engineer)|" +
    "data warehouse|etl|quantitative (analyst|developer|researcher)|cientista de dados|engenheiro de dados|analista de dados)\\b",
);
const QA = rx(
  "\\b(qa|quality assurance|quality engineer|test(ing)? (engineer|automation|analyst|lead|manager)|sdet|" +
    "(software )?(development )?engineer in test|automation tester|tester|testingenieur|analista de testes)\\b",
);
const DEVOPS = rx(
  "\\b(sre|site reliability|devops|platform engineer\\w*|infrastructure|infra\\b|cloud (engineer|architect)\\w*|" +
    "network engineer\\w*|systems engineer\\w*|system administrator|sysadmin|kubernetes|production engineer\\w*|" +
    "reliability|database administrator|dba|release engineer\\w*|build engineer\\w*|systemadministrator\\w*|infraestrutura)\\b",
);
const EMBEDDED = rx(
  "\\b(embedded|firmware|fpga|asic|hardware engineer\\w*|electronics?|robotics?|autonomy|autosar|ecu|rtos|" +
    "silicon|verification engineer|pcb|mechatronic\\w*|bsp|device driver\\w*|embarcad[oa]s?)\\b",
);
const SOFTWARE = rx(
  "\\b(software|developer|programmer|swe|sde|(back|front)[- ]?end|full[- ]?stack|mobile|ios|android|" +
    "web (developer|engineer)|application (developer|engineer)|engineering manager|" +
    "(java|python|golang|go|ruby|rails|node|react|\\.net|c\\+\\+|c#|php|kotlin|swift|scala|rust|typescript) " +
    "(developer|engineer)|game (developer|engineer|programmer)|\\w*entwickler\\w*|desenvolvedor\\w*|programador\\w*|" +
    "analista de sistemas|engenheiro de software|(staff|senior|principal|lead|junior) engineer|member of technical staff|engineer)\\b",
);
const NOT_SOFTWARE = rx(
  "\\b(mechanical|civil|chemical|process|manufacturing|field service|maintenance|structural|hvac|" +
    "construction|sales|solutions?|pre-?sales|customer|support|value|" +
    "electrical installation|facilities|quality control|industrial|environmental|petroleum)\\s+engineer",
);
const NON_TECH = rx(
  "\\b(sales|account executive|account manager|marketing|partner manager|partnerships?|alliances|" +
    "counsel|legal|lawyer|paralegal|recruit\\w*|talent|customer success|client value|business development|" +
    "bdr|sdr|go[- ]to[- ]market|gtm|communications|public policy|policy (lead|manager)|executive assistant|" +
    "accountant|payroll|office manager|copywriter)\\b",
);

const ORDER: [Family, RegExp, RegExp | null][] = [
  ["product", PRODUCT, null],
  ["video", VIDEO, null],
  ["design", DESIGN, NOT_DESIGN],
  ["security", SECURITY, NOT_SECURITY],
  ["data", DATA, null],
  ["qa", QA, null],
  ["devops", DEVOPS, null],
  ["embedded", EMBEDDED, null],
  ["software", SOFTWARE, NOT_SOFTWARE],
];

// Creative roles often sit in marketing teams ("Video Editor, Marketing"), so they
// are matched before the non-tech filter.
const CREATIVE: [Family, RegExp, RegExp | null][] = [["video", VIDEO, null], ["design", DESIGN, NOT_DESIGN]];

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
