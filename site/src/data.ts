// Knowledge files are bundled; job data is fetched at runtime so the daily
// workflow can refresh it without rebuilding the app logic.
import countriesJson from "../../knowledge/countries.json";
import tracksJson from "../../knowledge/tracks.json";
import skillsJson from "../../knowledge/skills.json";
import type { Country, Job, Market, Meta, Skill, Track } from "./types";

export const COUNTRIES = (countriesJson as { countries: Country[] }).countries;
export const COUNTRY = new Map(COUNTRIES.map((c) => [c.code, c]));
export const TRACKS = (tracksJson as unknown as { tracks: Track[] }).tracks;
export const TRACK = new Map(TRACKS.map((t) => [t.id, t]));
export const SKILLS = (skillsJson as { skills: Skill[] }).skills;
export const SKILL = new Map(SKILLS.map((s) => [s.id, s]));
export const KNOWLEDGE_AS_OF = (countriesJson as { asOf?: string }).asOf ?? "";

export function skillLabel(id: string): string {
  return SKILL.get(id)?.label ?? id.replace(/-/g, " ");
}

export interface Dataset {
  jobs: Job[];
  market: Market;
  meta: Meta;
}

function decodeJobs(raw: { fields: string[]; rows: unknown[][] }): Job[] {
  const idx = Object.fromEntries(raw.fields.map((f, i) => [f, i]));
  return raw.rows.map((r) => Object.fromEntries(Object.entries(idx).map(([k, i]) => [k, r[i]])) as unknown as Job);
}

export async function loadDataset(): Promise<Dataset> {
  const base = import.meta.env.BASE_URL + "data/";
  const get = async (name: string) => {
    const res = await fetch(base + name, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
    return res.json();
  };
  const [jobs, market, meta] = await Promise.all([get("jobs.json"), get("market.json"), get("meta.json")]);
  return { jobs: decodeJobs(jobs), market, meta };
}
