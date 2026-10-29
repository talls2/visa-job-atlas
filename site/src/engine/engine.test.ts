import { describe, expect, it } from "vitest";
import countriesJson from "../../../knowledge/countries.json";
import tracksJson from "../../../knowledge/tracks.json";
import { FAMILIES, type Answers, type Country, type Job, type Market, type Profile, type Track } from "../types";
import { rankCountries } from "./countries";
import { matchJobs, skillGaps } from "./jobs";
import { buildPlan } from "./plan";

const COUNTRIES = (countriesJson as unknown as { countries: Country[] }).countries;
const TRACKS = (tracksJson as unknown as { tracks: Track[] }).tracks;

const market: Market = {
  generatedAt: "",
  cells: {
    "DE|software": { jobs: 400, visaFriendly: 120, skills: { java: 90, kubernetes: 70, python: 60 } },
    "IE|software": { jobs: 200, visaFriendly: 80, skills: { java: 40, aws: 50 } },
    "JP|software": { jobs: 100, visaFriendly: 60, skills: { go: 30, aws: 20 } },
  },
};
const profile: Profile = {
  skills: ["python", "aws"], years: 4, level: "mid", degree: "bachelor", certs: [],
  languages: [{ code: "pt", level: "native" }, { code: "en", level: "fluent" }],
  families: ["software"], titles: [], textLength: 3000,
};
const answers: Answers = {
  citizenships: ["BR"], livesIn: "BR", targets: [], priorities: ["visa"], direction: "stay", family: "software",
  niche: "", learnLanguage: "maybe", hoursPerWeek: 8, budget: "low", horizon: 12, withFamily: false,
};
const job = (over: Partial<Job>): Job => ({
  id: "x", title: "Backend Engineer", company: "Acme", location: "Berlin", countries: ["DE"], url: "", posted: "",
  firstSeen: "", family: "software", seniority: "unspecified", remote: 0, visa: "unknown", registerIn: [], skills: [],
  langs: [], salary: "", ...over,
});

describe("knowledge files", () => {
  it("have every track and bilingual text", () => {
    expect(TRACKS.map((t) => t.id).sort()).toEqual([...FAMILIES].sort());
    const codes = new Set(COUNTRIES.map((c) => c.code));
    for (const t of TRACKS) {
      expect(t.name.en && t.name.pt && t.firstSponsoredRoles.en && t.firstSponsoredRoles.pt).toBeTruthy();
      for (const [code, note] of Object.entries(t.countryNotes ?? {})) {
        expect(codes.has(code)).toBe(true);
        expect(note.en && note.pt).toBeTruthy();
      }
    }
    for (const c of COUNTRIES) {
      expect(c.name.en && c.name.pt).toBeTruthy();
      expect(c.openness).toBeGreaterThanOrEqual(1);
      for (const r of c.routes) expect(r.summary.en && r.summary.pt).toBeTruthy();
    }
  });
});

describe("rankCountries", () => {
  it("puts free movement first for an EU citizen", () => {
    const eu = rankCountries(COUNTRIES, market, profile, { ...answers, citizenships: ["BR", "IT"] });
    expect(eu[0].freeMovement).toBe(true);
    expect(eu.find((f) => f.country.code === "DE")!.freeMovement).toBe(true);
    expect(eu.find((f) => f.country.code === "JP")!.freeMovement).toBe(false);
  });
  it("explains every score", () => {
    const fits = rankCountries(COUNTRIES, market, profile, answers);
    for (const f of fits) expect(f.score).toBe(f.reasons.reduce((s, r) => s + r.delta, 0));
  });
  it("respects a chosen country", () => {
    const base = rankCountries(COUNTRIES, market, profile, answers).find((f) => f.country.code === "NZ")!.score;
    const chosen = rankCountries(COUNTRIES, market, profile, { ...answers, targets: ["NZ"] }).find((f) => f.country.code === "NZ")!.score;
    expect(chosen).toBe(base + 15);
  });
});

describe("matchJobs", () => {
  const order = ["DE", "IE", "JP"];
  it("ranks visa signals and skills, and penalises missing languages", () => {
    const jobs = [
      job({ id: "a", visa: "explicit", skills: ["python", "aws"] }),
      job({ id: "b", visa: "unknown", skills: ["java"] }),
      job({ id: "c", visa: "explicit", skills: ["python"], langs: ["de"] }),
      job({ id: "d", family: "design" }),
      job({ id: "e", countries: ["US"] }),
    ];
    const m = matchJobs(jobs, profile, answers, order);
    expect(m.map((x) => x.job.id)).toEqual(["a", "b", "c"]);
    expect(m[2].languageBlock).toEqual(["de"]);
  });
  it("treats citizens' own countries as no-visa", () => {
    const m = matchJobs([job({ countries: ["PT"] })], profile, { ...answers, citizenships: ["PT"] }, order);
    expect(m[0].noVisaNeeded).toBe(true);
  });
  it("finds skill gaps by demand", () => {
    expect(skillGaps(market, ["DE", "IE"], "software", ["python"], 3).map((g) => g.id)).toEqual(["java", "kubernetes", "aws"]);
  });
});

describe("buildPlan", () => {
  it("builds three phases sized to the horizon", () => {
    const fits = rankCountries(COUNTRIES, market, profile, answers);
    const plan = buildPlan(TRACKS.find((t) => t.id === "software")!, fits, market, profile, { ...answers, horizon: 6 });
    expect(plan.phases).toHaveLength(3);
    expect(plan.phases[0].title.en).toBe("Month 1");
    expect(plan.phases.every((p) => p.items.length > 0)).toBe(true);
    expect(plan.top).toHaveLength(3);
  });
});
