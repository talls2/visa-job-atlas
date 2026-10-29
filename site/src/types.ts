// Shapes of the knowledge files and generated data (see docs/DATA.md).

export type Lang = "en" | "pt";
export type L10n = { en: string; pt: string };

export type Family =
  | "security" | "software" | "data" | "devops" | "embedded" | "qa" | "product" | "design" | "video"
  | "mechanical" | "electrical" | "civil" | "marketing" | "sales" | "finance" | "operations" | "people" | "healthcare";
export const FAMILIES: Family[] = [
  "software", "data", "devops", "security", "embedded", "qa", "product", "design", "video",
  "mechanical", "electrical", "civil", "marketing", "sales", "finance", "operations", "people", "healthcare",
];

export type Level = "entry" | "junior" | "mid" | "senior" | "lead";
export type Degree = "none" | "technical" | "bachelor" | "master" | "phd";

export interface Route {
  id: string;
  name: L10n;
  summary: L10n;
  salaryMin: { amount: number; currency: string; period: string; note?: L10n } | null;
  degree: "required" | "or-experience" | "not-required";
  employerSponsored: boolean;
  processing: L10n | null;
  source: string;
}

export interface Country {
  code: string;
  name: L10n;
  bloc: "eu" | "ch" | null;
  openness: number;
  opennessNote: L10n;
  routes: Route[];
  residencePath: L10n;
  language: {
    code: string;
    name: L10n;
    importance: "low" | "medium" | "high";
    note: L10n;
    learning: { target: string; exam: string; hours: L10n } | null;
  } | null;
  englishWorkplace: "high" | "medium" | "low";
  catches: L10n[];
  recentChanges: L10n[];
  sponsorRegister: { name: L10n; url: string } | null;
  jobBoards: { name: string; url: string }[];
  cvTips: L10n;
  sources: string[];
}

export interface Cert {
  name: string;
  provider: string;
  level: "entry" | "mid" | "senior";
  cost: string;
  why: L10n;
  url: string;
}

export interface Track {
  id: Family;
  name: L10n;
  summary: L10n;
  niches: { id: string; name: L10n; summary: L10n; keywords: string[] }[];
  coreSkills: string[];
  certs: Cert[];
  projects: { title: L10n; description: L10n; level: "entry" | "mid" }[];
  firstSponsoredRoles: L10n;
  switchTips: Partial<Record<Family, L10n>>;
  weeklyQuests: L10n[];
  milestones: { m3: L10n[]; m6: L10n[]; m12: L10n[] };
  // Licensing, recognition and route notes for this field in specific countries.
  countryNotes?: Record<string, L10n>;
}

export interface Skill {
  id: string;
  label: string;
  patterns: string[];
  families: Family[];
}

export type Visa =
  | "explicit" | "conditional" | "register" | "employer-yes" | "relocation" | "unknown" | "blocked" | "employer-no";

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  countries: string[];
  url: string;
  posted: string;
  firstSeen: string;
  family: Family;
  seniority: string;
  remote: number;
  visa: Visa;
  registerIn: string[];
  skills: string[];
  langs: string[];
  salary: string;
}

export interface MarketCell { jobs: number; visaFriendly: number; englishOk?: number; skills: Record<string, number> }
export interface Market { generatedAt: string; cells: Record<string, MarketCell> }
export interface Meta {
  generatedAt: string;
  jobs: number;
  sources: { name: string; kind: string; ok: boolean; listed: number; kept: number; error: string }[];
  registers: { source: string; country: string; rows: number; loadedAt: string }[];
}

/** What we read from the CV, editable by the user. */
export interface Profile {
  skills: string[];
  years: number;
  level: Level;
  degree: Degree;
  certs: string[];
  languages: { code: string; level: "basic" | "intermediate" | "fluent" | "native" }[];
  families: Family[];          // detected, most likely first
  titles: string[];            // job titles found
  textLength: number;
}

export type Priority = "visa" | "english" | "salary" | "residence" | "quality";

/** Interview answers. */
export interface Answers {
  citizenships: string[];      // ISO-2
  livesIn: string;             // ISO-2
  targets: string[];           // ISO-2, empty = suggest
  priorities: Priority[];
  direction: "stay" | "switch" | "unsure";
  family: Family;              // the track to plan for
  niche: string;
  learnLanguage: "yes" | "maybe" | "no";
  hoursPerWeek: number;
  budget: "none" | "low" | "medium" | "high";
  horizon: 6 | 12 | 24;
  withFamily: boolean;
}
