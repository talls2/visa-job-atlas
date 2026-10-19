// Scores open postings for one person: role family, visa signal, country,
// seniority, skills overlap and language requirements.
import type { Answers, Job, Level, Profile, Visa } from "../types";
import { EU_EEA } from "./countries";

export interface JobMatch {
  job: Job;
  score: number;
  matchedSkills: string[];
  missingSkills: string[];
  noVisaNeeded: boolean;
  openMarket: boolean;         // no sponsor register in that country: any employer can file a permit
  languageBlock: string[];     // required languages the person doesn't speak
  seniorityGap: number;        // job level minus person level, in steps
}

const VISA_POINTS: Record<Visa, number> = {
  explicit: 35, conditional: 15, register: 20, "employer-yes": 15, relocation: 8, unknown: 0, blocked: -60, "employer-no": -50,
};

const LEVEL_STEP: Record<Level, number> = { entry: 0, junior: 1, mid: 2, senior: 3, lead: 4 };
const JOB_STEP: Record<string, number | null> = {
  intern: 0, "new-grad": 0, junior: 1, unspecified: null, senior: 3, lead: 4, staff: 4, principal: 5, manager: 4,
};

export function matchJobs(
  jobs: Job[], profile: Profile, answers: Answers, countryOrder: string[], registerCountries: Set<string> = new Set(), limit = 3000,
): JobMatch[] {
  const mine = new Set(profile.skills);
  const myLangs = new Set(profile.languages.filter((l) => l.level !== "basic").map((l) => l.code));
  const euCitizen = answers.citizenships.some((c) => EU_EEA.has(c));
  const top = new Set(countryOrder.slice(0, 6));
  const me = LEVEL_STEP[profile.level];
  const today = Date.now();

  const out: JobMatch[] = [];
  for (const job of jobs) {
    if (job.family !== answers.family) continue;
    // The point is to move: a role in the country you already live in doesn't count.
    const abroad = job.countries.filter((c) => c !== answers.livesIn);
    if (job.countries.length && !abroad.length) continue;
    const noVisaNeeded = abroad.some(
      (c) => answers.citizenships.includes(c) || (euCitizen && (EU_EEA.has(c) || c === "CH")),
    );
    if (!abroad.some((c) => top.has(c)) && !noVisaNeeded && !(job.remote && job.countries.length === 0)) continue;

    let score = 30;
    const openMarket = !noVisaNeeded && job.visa === "unknown" && registerCountries.size > 0 && abroad.some((c) => !registerCountries.has(c));
    score += noVisaNeeded ? 35 : openMarket ? 12 : VISA_POINTS[job.visa] ?? 0;
    if (job.visa === "register" && job.countries.some((c) => job.registerIn.includes(c))) score += 5;
    if (job.countries.some((c) => answers.targets.includes(c))) score += 10;
    else if (job.countries.some((c) => top.has(c))) score += 5;

    const step = JOB_STEP[job.seniority] ?? null;
    const gap = step === null ? 0 : step - me;
    score -= Math.abs(gap) * 7 + (gap > 1 ? 6 : 0);

    const matchedSkills = job.skills.filter((s) => mine.has(s));
    const missingSkills = job.skills.filter((s) => !mine.has(s));
    if (job.skills.length) score += Math.round((matchedSkills.length / job.skills.length) * 25);

    const languageBlock = job.langs.filter((l) => !myLangs.has(l));
    // A role you can't do without a language you don't speak ranks below any other.
    score -= languageBlock.length * 80;

    const posted = Date.parse(job.posted || job.firstSeen);
    if (!Number.isNaN(posted) && today - posted < 14 * 864e5) score += 5;

    out.push({ job, score, matchedSkills, missingSkills, noVisaNeeded, openMarket, languageBlock, seniorityGap: gap });
  }
  return out.sort((a, b) => b.score - a.score).slice(0, limit);
}

// Too general to be a useful learning goal.
const GENERIC = new Set(["security-fundamentals", "git", "agile", "excel", "leadership"]);

/** Skills the market asks for in these countries that the CV doesn't show, by demand. */
export function skillGaps(
  market: { cells: Record<string, { skills: Record<string, number> }> },
  countries: string[],
  family: string,
  have: string[],
  n = 8,
): { id: string; count: number }[] {
  const mine = new Set(have);
  const totals = new Map<string, number>();
  for (const c of countries) {
    const cell = market.cells[`${c}|${family}`];
    if (!cell) continue;
    for (const [id, count] of Object.entries(cell.skills)) totals.set(id, (totals.get(id) ?? 0) + count);
  }
  return [...totals.entries()]
    .filter(([id]) => !mine.has(id) && !GENERIC.has(id))
    .sort((a, b) => b[1] - a[1])
    .slice(0, n)
    .map(([id, count]) => ({ id, count }));
}
