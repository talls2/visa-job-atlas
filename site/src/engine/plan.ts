// Builds the personal plan: phases with concrete items, sized to the person's
// horizon, weekly hours and budget, from the track knowledge and live demand.
import type { Answers, Cert, Country, L10n, Market, Profile, Track } from "../types";
import type { CountryFit } from "./countries";
import { skillGaps } from "./jobs";

export type ItemKind = "profile" | "skill" | "cert" | "project" | "language" | "network" | "apply" | "visa";
export interface PlanItem { kind: ItemKind; text: L10n; detail?: L10n; url?: string }
export interface Phase { id: string; title: L10n; items: PlanItem[] }
export interface Plan {
  track: Track;
  top: CountryFit[];
  gaps: { id: string; count: number }[];
  certs: Cert[];
  language: { country: Country; target: string; exam: string; hours: L10n } | null;
  phases: Phase[];
  weekly: L10n[];
  switchTip: L10n | null;
  connectionNote: L10n;
}

const L = (en: string, pt: string): L10n => ({ en, pt });

function windows(h: Answers["horizon"]): [L10n, L10n, L10n] {
  if (h === 6) return [L("Month 1", "Mês 1"), L("Months 2-3", "Meses 2-3"), L("Months 4-6", "Meses 4-6")];
  if (h === 24) return [L("Months 1-6", "Meses 1-6"), L("Months 7-12", "Meses 7-12"), L("Months 13-24", "Meses 13-24")];
  return [L("Months 1-3", "Meses 1-3"), L("Months 4-6", "Meses 4-6"), L("Months 7-12", "Meses 7-12")];
}

function pickCerts(track: Track, profile: Profile, budget: Answers["budget"]): Cert[] {
  const want: Cert["level"][] =
    profile.level === "entry" || profile.level === "junior" ? ["entry", "mid"] : profile.level === "mid" ? ["mid", "entry", "senior"] : ["senior", "mid"];
  const have = new Set(profile.certs.map((c) => c.toLowerCase()));
  const ranked = track.certs
    .filter((c) => !have.has(c.name.toLowerCase()))
    .sort((a, b) => want.indexOf(a.level) - want.indexOf(b.level))
    .filter((c) => want.includes(c.level));
  const n = budget === "none" ? 1 : budget === "low" ? 2 : 3;
  return ranked.slice(0, n);
}

export function buildPlan(
  track: Track, fits: CountryFit[], market: Market, profile: Profile, answers: Answers, label: (id: string) => string = (id) => id,
): Plan {
  const top = fits.slice(0, 3);
  const topCodes = top.map((f) => f.country.code);
  const gaps = skillGaps(market, topCodes, track.id, profile.skills, 8);
  const certs = pickCerts(track, profile, answers.budget);
  const [w1, w2, w3] = windows(answers.horizon);
  const light = answers.hoursPerWeek < 6;

  // Language: the best-ranked country whose language matters and the CV doesn't show it.
  const langFit = top.find((f) => f.languageGap && f.country.language?.learning && !f.freeMovement) ?? top.find((f) => f.languageGap && f.country.language?.learning);
  const language =
    langFit && answers.learnLanguage !== "no" && langFit.country.language?.learning
      ? { country: langFit.country, target: langFit.country.language.learning.target, exam: langFit.country.language.learning.exam, hours: langFit.country.language.learning.hours }
      : null;

  const projects = track.projects.filter((p) => (profile.level === "entry" || profile.level === "junior" ? true : p.level === "mid") || track.projects.length <= 3);
  const gapLabel = (n: number) => gaps.slice(1, n).map((g) => label(g.id)).join(", ");

  const p1: PlanItem[] = [
    { kind: "profile", text: L("Rewrite your CV and LinkedIn for the target market", "Reescreva seu CV e LinkedIn para o mercado-alvo"),
      detail: top[0] ? top[0].country.cvTips : undefined },
    { kind: "profile", text: L("Put your public work in one place: GitHub profile README, pinned projects and a simple website", "Reúna seu trabalho público em um lugar: README do perfil no GitHub, projetos fixados e um site simples") },
  ];
  if (gaps.length)
    p1.push({ kind: "skill", text: L(`Start the most-requested skill you're missing: ${label(gaps[0].id)}`, `Comece pela habilidade mais pedida que você ainda não mostra: ${label(gaps[0].id)}`),
      detail: L(`Seen in ${gaps[0].count} open postings in your target countries.`, `Aparece em ${gaps[0].count} vagas abertas nos seus países-alvo.`) });
  if (projects[0]) p1.push({ kind: "project", text: projects[0].title, detail: projects[0].description });
  if (language)
    p1.push({ kind: "language", text: L(`Start ${language.country.language!.name.en}: a daily 30-45 minute habit`, `Comece ${language.country.language!.name.pt}: hábito diário de 30-45 minutos`),
      detail: L(`Target ${language.target} (${language.exam}). ${language.hours.en}`, `Meta ${language.target} (${language.exam}). ${language.hours.pt}`) });
  p1.push({ kind: "network", text: L("Join one community in your field and send 10 targeted connection requests a week", "Entre em uma comunidade da sua área e envie 10 pedidos de conexão direcionados por semana") });
  track.milestones.m3.slice(0, light ? 1 : 2).forEach((m) => p1.push({ kind: "project", text: m }));

  const p2: PlanItem[] = [];
  if (certs[0]) p2.push({ kind: "cert", text: L(`Earn ${certs[0].name} (${certs[0].provider})`, `Tire a ${certs[0].name} (${certs[0].provider})`), detail: certs[0].why, url: certs[0].url });
  if (gaps.length > 1) p2.push({ kind: "skill", text: L(`Close the next gaps: ${gapLabel(4)}`, `Feche as próximas lacunas: ${gapLabel(4)}`) });
  if (projects[1]) p2.push({ kind: "project", text: projects[1].title, detail: projects[1].description });
  p2.push({ kind: "apply", text: L("Start applying: 2-3 tailored applications a week to roles with a visa signal", "Comece a se candidatar: 2-3 candidaturas personalizadas por semana para vagas com sinal de visto") });
  track.milestones.m6.slice(0, light ? 1 : 2).forEach((m) => p2.push({ kind: "project", text: m }));

  const p3: PlanItem[] = [];
  if (certs[1]) p3.push({ kind: "cert", text: L(`Earn ${certs[1].name} (${certs[1].provider})`, `Tire a ${certs[1].name} (${certs[1].provider})`), detail: certs[1].why, url: certs[1].url });
  if (language) p3.push({ kind: "language", text: L(`Book the ${language.exam} exam at ${language.target}`, `Agende a prova ${language.exam} no nível ${language.target}`) });
  for (const f of top.filter((f) => !f.freeMovement).slice(0, 2)) {
    const r = f.country.routes[0];
    if (r)
      p3.push({ kind: "visa", text: L(`${f.country.name.en}: prepare for the ${r.name.en}`, `${f.country.name.pt}: prepare-se para o ${r.name.pt}`), detail: r.summary, url: r.source });
  }
  if (answers.withFamily && top.some((f) => !f.freeMovement))
    p3.push({ kind: "visa", text: L(
      "Check the family rules of your route: whether your partner can work and how long dependants' visas take",
      "Confira as regras para família da sua rota: se seu parceiro(a) pode trabalhar e quanto demoram os vistos de dependentes",
    ) });
  p3.push({ kind: "apply", text: L("Track every application and aim for a 10%+ interview rate; adjust your CV if you're below it", "Registre cada candidatura e mire em 10%+ de entrevistas; ajuste o CV se ficar abaixo") });
  track.milestones.m12.slice(0, light ? 1 : 3).forEach((m) => p3.push({ kind: "project", text: m }));

  const fromFamily = profile.families.find((f) => f !== track.id);
  const switchTip = answers.direction === "switch" && fromFamily ? track.switchTips[fromFamily] ?? null : null;

  const field = track.name;
  const connectionNote = L(
    `Hi {name}, I read your {post/talk} on {topic}. I'm a ${field.en.toLowerCase()} professional with ${Math.round(profile.years)}+ years of experience, looking at ${top[0]?.country.name.en ?? "your country"}. I'd love to follow your work and learn from your team.`,
    `Hi {name}, I read your {post/talk} on {topic}. I work in ${field.en.toLowerCase()} with ${Math.round(profile.years)}+ years of experience and I'm looking at ${top[0]?.country.name.en ?? "your country"}. I'd love to follow your work and learn from your team.`,
  );

  return {
    track, top, gaps, certs, language, switchTip, connectionNote,
    weekly: track.weeklyQuests,
    phases: [
      { id: "p1", title: w1, items: p1 },
      { id: "p2", title: w2, items: p2 },
      { id: "p3", title: w3, items: p3 },
    ],
  };
}
