// Optional: asks Claude to write the plan in prose, using the person's own
// Anthropic API key. The key and the CV go straight from the browser to the
// Anthropic API; this site has no server.
import Anthropic from "@anthropic-ai/sdk";
import type { Answers, Lang, Profile } from "../types";
import type { Plan } from "./plan";
import type { JobMatch } from "./jobs";

export const MODELS = [
  { id: "claude-opus-5-5", label: "Claude Opus 5.5" },
  { id: "claude-sonnet-5-5", label: "Claude Sonnet 5.5" },
  { id: "claude-haiku-5-5", label: "Claude Haiku 5.5" },
];

const SYSTEM = `You are a careful career and immigration-pathway advisor for professionals (tech, engineering, business, health and creative fields) who want a visa-sponsored job abroad.
You receive: the person's CV text, their answers to an intake interview, and facts computed by the Visa Job Atlas app
(country ranking with reasons, visa routes and thresholds, live job-market demand, matching open postings, skill gaps,
and a draft phased plan). Write a personal plan they can act on this week.

Rules:
- Ground every claim in the facts provided. Quote salary floors, routes and numbers exactly as given; never invent new ones.
  If something important is unknown, say what to check and where.
- Be concrete and specific to this person's CV: name their real strengths, the gaps that matter, and the 2-3 countries to focus on and why.
- Structure: 1) Where you stand (3-5 bullets). 2) Best countries for you, with the visa route for each. 3) The plan by phase,
  with measurable milestones. 4) This week: 5 concrete first actions. 5) Risks and how to reduce them.
- Plain, direct language. Markdown headings and bullets. No legal advice: for visa specifics, point to the official source.
- Write in the language requested.`;

export interface ClaudeInput {
  cvText: string;
  profile: Profile;
  answers: Answers;
  plan: Plan;
  matches: JobMatch[];
  lang: Lang;
}

function factsFor({ profile, answers, plan, matches, lang }: ClaudeInput) {
  return {
    language: lang === "pt" ? "Brazilian Portuguese" : "English",
    profile,
    answers,
    track: { id: plan.track.id, name: plan.track.name.en, firstSponsoredRoles: plan.track.firstSponsoredRoles.en },
    topCountries: plan.top.map((f) => ({
      code: f.country.code,
      name: f.country.name.en,
      score: f.score,
      freeMovement: f.freeMovement,
      demand: f.demand,
      reasons: f.reasons.map((r) => `${r.delta > 0 ? "+" : ""}${r.delta}: ${r.text.en}`),
      routes: f.country.routes.map((r) => ({
        name: r.name.en, summary: r.summary.en, salaryMin: r.salaryMin, degree: r.degree, source: r.source,
      })),
      residencePath: f.country.residencePath.en,
      language: f.country.language ? { name: f.country.language.name.en, importance: f.country.language.importance } : null,
      catches: f.country.catches.map((c) => c.en),
      recentChanges: f.country.recentChanges.map((c) => c.en),
    })),
    skillGaps: plan.gaps,
    suggestedCerts: plan.certs.map((c) => ({ name: c.name, provider: c.provider, cost: c.cost })),
    languagePlan: plan.language ? { country: plan.language.country.name.en, target: plan.language.target, exam: plan.language.exam } : null,
    draftPhases: plan.phases.map((p) => ({ when: p.title.en, items: p.items.map((i) => i.text.en) })),
    topMatchingJobs: matches.slice(0, 15).map((m) => ({
      title: m.job.title, company: m.job.company, location: m.job.location, visa: m.job.visa,
      noVisaNeeded: m.noVisaNeeded, matchedSkills: m.matchedSkills, url: m.job.url,
    })),
  };
}

export async function writePlanWithClaude(
  apiKey: string,
  model: string,
  input: ClaudeInput,
  onText: (chunk: string) => void,
  signal?: AbortSignal,
): Promise<{ stopReason: string | null }> {
  const client = new Anthropic({ apiKey, dangerouslyAllowBrowser: true });
  const facts = JSON.stringify(factsFor(input), null, 1);
  const params = {
    model,
    max_tokens: 16000,
    system: SYSTEM,
    output_config: { effort: "medium" as const },
    messages: [
      {
        role: "user" as const,
        content:
          `<cv>\n${input.cvText.slice(0, 60000)}\n</cv>\n\n<facts>\n${facts}\n</facts>\n\n` +
          `Write my plan in ${input.lang === "pt" ? "Brazilian Portuguese" : "English"}.`,
      },
    ],
  };
  // Opus/Sonnet 5.5 can decline in rare safety-classifier false positives; the
  // server-side fallback retries on another model inside the same call.
  const withFallback = model !== "claude-haiku-5-5";
  const stream = withFallback
    ? client.beta.messages.stream(
        { ...params, betas: ["server-side-fallback-2026-07-01"], fallbacks: "default" } as unknown as Parameters<
          typeof client.beta.messages.stream
        >[0],
        { signal },
      )
    : client.messages.stream(params, { signal });

  for await (const event of stream as AsyncIterable<{ type: string; delta?: { type: string; text?: string } }>) {
    if (event.type === "content_block_delta" && event.delta?.type === "text_delta" && event.delta.text) onText(event.delta.text);
  }
  const final = await (stream as { finalMessage(): Promise<{ stop_reason: string | null }> }).finalMessage();
  return { stopReason: final.stop_reason };
}
