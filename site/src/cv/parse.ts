// Reads a CV's plain text into a Profile. Heuristic by design: the user reviews
// and corrects everything on the next screen. Works on English and Portuguese CVs.
import type { Degree, Family, Level, Profile, Skill } from "../types";
import { FAMILIES } from "../types";
import { jobFamily } from "./family";

// ------------------------------------------------------------------ skills
export function compileSkills(skills: Skill[]) {
  return skills.map((s) => ({
    skill: s,
    re: new RegExp("(?<![\\w+#.])(" + s.patterns.join("|") + ")(?![\\w+#])", "gi"),
  }));
}

export function findSkills(text: string, compiled: ReturnType<typeof compileSkills>): string[] {
  const hits: [number, string][] = [];
  for (const { skill, re } of compiled) {
    const n = (text.match(re) || []).length;
    if (n) hits.push([n, skill.id]);
  }
  hits.sort((a, b) => b[0] - a[0] || a[1].localeCompare(b[1]));
  return hits.map((h) => h[1]);
}

// ----------------------------------------------------------- experience years
const MONTHS: Record<string, number> = {
  jan: 0, january: 0, janeiro: 0, feb: 1, february: 1, fev: 1, fevereiro: 1, mar: 2, march: 2, março: 2, marco: 2,
  apr: 3, april: 3, abr: 3, abril: 3, may: 4, mai: 4, maio: 4, jun: 5, june: 5, junho: 5, jul: 6, july: 6, julho: 6,
  aug: 7, august: 7, ago: 7, agosto: 7, sep: 8, sept: 8, september: 8, set: 8, setembro: 8, oct: 9, october: 9,
  out: 9, outubro: 9, nov: 10, november: 10, novembro: 10, dec: 11, december: 11, dez: 11, dezembro: 11,
};
const MONTH_RX = Object.keys(MONTHS).sort((a, b) => b.length - a.length).join("|");
const NOW_RX = "present|current|now|today|ongoing|atual|atualmente|presente|o momento|hoje|heute|actualidad";
const POINT = `(?:(?:(${MONTH_RX})\\.?(?:\\s+de)?\\s+|(\\d{1,2})[/.-])?((?:19|20)\\d{2}))`;
const RANGE = new RegExp(`${POINT}\\s*(?:-|–|—|to|até|a|bis)\\s*(?:${POINT}|(${NOW_RX}))`, "gi");

type Span = [number, number]; // months since year 0

function toMonth(mName: string | undefined, mNum: string | undefined, year: string, end: boolean): number {
  const y = parseInt(year, 10);
  let m = end ? 11 : 0;
  if (mName) m = MONTHS[mName.toLowerCase()] ?? m;
  else if (mNum) m = Math.min(11, Math.max(0, parseInt(mNum, 10) - 1));
  return y * 12 + m;
}

const SECTION_EDU = /^\s*(education|academic|formação|formacao|educação|educacao|escolaridade|qualifications)\b/i;
const SECTION_EXP = /^\s*(experience|work experience|professional experience|employment|experiência|experiencia|histórico profissional|work history)\b/i;
const SECTION_OTHER = /^\s*(skills|habilidades|competências|competencias|certifications?|certificações|certificados|languages|idiomas|projects|projetos|courses|cursos|summary|resumo|about|sobre|awards|volunteer)\b/i;

/** Splits the CV into experience text (if a section is found) and the rest. */
function experienceText(text: string): string {
  const lines = text.split(/\n/);
  let mode: "exp" | "edu" | "other" | "none" = "none";
  const exp: string[] = [];
  let sawExp = false;
  for (const line of lines) {
    if (line.length < 60 && SECTION_EXP.test(line)) { mode = "exp"; sawExp = true; continue; }
    if (line.length < 60 && SECTION_EDU.test(line)) { mode = "edu"; continue; }
    if (line.length < 60 && SECTION_OTHER.test(line)) { mode = "other"; continue; }
    if (mode === "exp") exp.push(line);
  }
  if (sawExp && exp.length) return exp.join("\n");
  // No headers: drop lines that look like education.
  return lines.filter((l) => !DEGREE_ANY.test(l)).join("\n");
}

export function experienceYears(text: string, now = new Date()): number {
  const nowM = now.getFullYear() * 12 + now.getMonth();
  const spans: Span[] = [];
  for (const m of experienceText(text).matchAll(RANGE)) {
    const start = toMonth(m[1], m[2], m[3], false);
    const end = m[7] ? nowM : m[6] ? toMonth(m[4], m[5], m[6], true) : nowM;
    if (end >= start && start > 1970 * 12 && start <= nowM && end - start < 50 * 12) spans.push([start, Math.min(end, nowM)]);
  }
  spans.sort((a, b) => a[0] - b[0]);
  let total = 0;
  let cur: Span | null = null;
  for (const s of spans) {
    if (!cur || s[0] > cur[1]) {
      if (cur) total += cur[1] - cur[0] + 1;
      cur = [s[0], s[1]];
    } else cur[1] = Math.max(cur[1], s[1]);
  }
  if (cur) total += cur[1] - cur[0] + 1;
  return Math.round((total / 12) * 10) / 10;
}

// ---------------------------------------------------------------- degree
const DEGREE_PATTERNS: [Degree, RegExp][] = [
  ["phd", /\b(ph\.?\s?d|doctorate|doutorado|doutor|dr\. rer)\b/i],
  ["master", /\b(master'?s?|m\.?\s?sc|msc|m\.s\.|mba|mestrado|mestre|meng|m\.eng)\b/i],
  ["bachelor", /\b(bachelor'?s?|b\.?\s?sc|bsc|b\.s\.|b\.a\.|ba in|beng|b\.eng|bacharel|bacharelado|licenciatura|graduação em|graduacao em|engenharia d[aoe])\b/i],
  ["technical", /\b(associate degree|tecnólogo|tecnologo|técnico em|tecnico em|hnd|diploma in)\b/i],
];
const DEGREE_ANY = /\b(bachelor|b\.?\s?sc|master|m\.?\s?sc|mba|ph\.?\s?d|bacharel|licenciatura|tecnólogo|mestrado|doutorado|universit|university|faculdade|college)\b/i;

export function highestDegree(text: string): Degree {
  for (const [deg, re] of DEGREE_PATTERNS) if (re.test(text)) return deg;
  return "none";
}

// ----------------------------------------------------------------- certs
const CERTS: [string, RegExp][] = [
  ["CompTIA Security+", /security\+/i], ["CompTIA Network+", /network\+/i], ["CompTIA A+", /comptia a\+/i],
  ["CISSP", /\bcissp\b/i], ["CISM", /\bcism\b/i], ["CISA", /\bcisa\b/i], ["CEH", /\bceh\b|certified ethical hacker/i],
  ["OSCP", /\boscp\b/i], ["OSWE", /\boswe\b/i], ["eJPT", /\bejpt\b/i], ["PNPT", /\bpnpt\b/i], ["CRTP", /\bcrtp\b/i],
  ["GIAC", /\bgiac\b|\bgsec\b|\bgcih\b|\bgpen\b/i], ["ISO 27001 Lead Auditor/Implementer", /27001 (lead )?(auditor|implementer)/i],
  ["AWS Certified", /aws certified|aws solutions architect|aws developer associate/i], ["Azure certification", /\baz-\d{3}\b|azure (fundamentals|administrator|developer|solutions architect)/i],
  ["Google Cloud certification", /google cloud (certified|professional|associate)/i], ["CKA", /\bcka\b|certified kubernetes administrator/i],
  ["CKAD", /\bckad\b/i], ["Terraform Associate", /terraform associate/i], ["CCNA", /\bccna\b/i], ["CCNP", /\bccnp\b/i],
  ["PMP", /\bpmp\b/i], ["Scrum (PSM/CSM)", /\b(psm|csm)\b|scrum master/i], ["CSPO/PSPO", /\b(cspo|pspo)\b/i],
  ["ISTQB", /\bistqb\b/i], ["Oracle Java (OCP)", /\bocp\b|oracle certified/i], ["Databricks", /databricks certified/i],
  ["TensorFlow Developer", /tensorflow developer certificate/i], ["ITIL", /\bitil\b/i], ["TOGAF", /\btogaf\b/i],
];

export function findCerts(text: string): string[] {
  return CERTS.filter(([, re]) => re.test(text)).map(([name]) => name);
}

// -------------------------------------------------------------- languages
const LANGS: [string, RegExp][] = [
  ["en", /\b(english|inglês|ingles)\b/i], ["pt", /\b(portuguese|português|portugues)\b/i],
  ["es", /\b(spanish|espanhol|español)\b/i], ["de", /\b(german|alemão|alemao|deutsch)\b/i],
  ["fr", /\b(french|francês|frances)\b/i], ["it", /\b(italian|italiano)\b/i], ["ja", /\b(japanese|japonês|japones)\b/i],
  ["nl", /\b(dutch|holandês|holandes)\b/i], ["zh", /\b(mandarin|chinese|chinês|mandarim)\b/i], ["ko", /\b(korean|coreano)\b/i],
  ["sv", /\b(swedish|sueco)\b/i], ["pl", /\b(polish|polonês)\b/i],
];
const LEVELS: [Profile["languages"][number]["level"], RegExp][] = [
  ["native", /native|nativo|materna|mother tongue|\bc2\b/i],
  ["fluent", /fluent|fluente|fluência|fluencia|advanced|avançado|avancado|proficient|full professional|\bc1\b/i],
  ["intermediate", /intermediate|intermediário|intermediario|conversational|\bb1\b|\bb2\b/i],
  ["basic", /basic|básico|basico|elementary|beginner|iniciante|\ba1\b|\ba2\b/i],
];

export function findLanguages(text: string): Profile["languages"] {
  const out: Profile["languages"] = [];
  const lines = text.split(/\n/);
  for (const [code, re] of LANGS) {
    const line = lines.find((l) => re.test(l) && l.length < 160);
    if (!line) continue;
    // Look for a level on the same line, right after the language name.
    const after = line.slice(line.search(re));
    const level = LEVELS.find(([, lr]) => lr.test(after.slice(0, 60)))?.[0];
    out.push({ code, level: level ?? (code === "en" ? "fluent" : "intermediate") });
  }
  return out;
}

// ----------------------------------------------------------------- level
export function levelFromYears(years: number, text = ""): Level {
  const titleBoost = /\b(staff|principal|lead|head of|tech lead|líder|lider|gerente|manager)\b/i.test(text);
  if (years >= 9 || (years >= 7 && titleBoost)) return "lead";
  if (years >= 5) return "senior";
  if (years >= 2.5) return "mid";
  if (years >= 1) return "junior";
  return "entry";
}

// ------------------------------------------------------------------ main
export function parseCv(text: string, skills: Skill[], now = new Date()): Profile {
  const compiled = compileSkills(skills);
  const found = findSkills(text, compiled);
  const years = experienceYears(text, now);

  // Families: job-title lines count most, skills add a little.
  const famScore: Record<Family, number> = Object.fromEntries(FAMILIES.map((f) => [f, 0])) as Record<Family, number>;
  const titles: string[] = [];
  for (const line of text.split(/\n/)) {
    // Titles are short lines, not sentences or certification names.
    if (line.length > 70 || line.length < 4 || /[.;:]\s*$/.test(line) || /certif/i.test(line) || line.split(/\s+/).length > 9 || findCerts(line).length) continue;
    const fam = jobFamily(line);
    if (fam) {
      famScore[fam] += 3;
      if (titles.length < 8 && !titles.includes(line.trim())) titles.push(line.trim());
    }
  }
  const byId = new Map(skills.map((s) => [s.id, s]));
  for (const id of found) for (const f of byId.get(id)?.families ?? []) famScore[f] += 1 / (byId.get(id)!.families.length || 1);
  const families = FAMILIES.filter((f) => famScore[f] > 0).sort((a, b) => famScore[b] - famScore[a]);

  return {
    skills: found,
    years,
    level: levelFromYears(years, titles.join(" ")),
    degree: highestDegree(text),
    certs: findCerts(text),
    languages: findLanguages(text),
    families: families.length ? families : ["software"],
    titles,
    textLength: text.length,
  };
}
