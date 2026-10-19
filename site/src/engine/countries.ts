// Ranks countries for one person. Every point added or removed carries a reason
// so the result can explain itself.
import type { Answers, Country, Family, L10n, Market, Profile } from "../types";

export interface Reason { text: L10n; delta: number }
export interface CountryFit {
  country: Country;
  score: number;
  reasons: Reason[];
  freeMovement: boolean;       // no work visa needed (citizen, or EU/EEA/CH citizen in that bloc)
  demand: { jobs: number; visaFriendly: number; englishOk: number; reachable: number };
  languageGap: boolean;
}

// EU/EEA member states (ISO-2) whose citizens move freely within the "eu" bloc and to Switzerland.
export const EU_EEA = new Set([
  "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT",
  "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE", "IS", "LI", "NO",
]);

const L = (en: string, pt: string): L10n => ({ en, pt });

// Share of English-language postings assumed reachable where no public sponsor
// register exists (DE, JP, SE...): any employer there can file a work permit,
// so a missing register match says nothing about sponsorship.
const OPEN_MARKET_SHARE = 0.3;

export function demandFor(market: Market, code: string, families: Family[], hasRegister = true) {
  let jobs = 0;
  let visaFriendly = 0;
  let englishOk = 0;
  for (const f of families) {
    const cell = market.cells[`${code}|${f}`];
    if (cell) {
      jobs += cell.jobs;
      visaFriendly += cell.visaFriendly;
      englishOk += cell.englishOk ?? cell.jobs;
    }
  }
  const reachable = hasRegister ? visaFriendly : visaFriendly + Math.round(OPEN_MARKET_SHARE * Math.max(0, englishOk - visaFriendly));
  return { jobs, visaFriendly, englishOk, reachable };
}

function speaks(profile: Profile, code: string, min: "intermediate" | "fluent" = "intermediate") {
  const order = ["basic", "intermediate", "fluent", "native"];
  return profile.languages.some((l) => l.code === code && order.indexOf(l.level) >= order.indexOf(min));
}

export function rankCountries(
  countries: Country[], market: Market, profile: Profile, answers: Answers, registerCountries: Set<string> = new Set(),
): CountryFit[] {
  const fams = [answers.family];
  const euCitizen = answers.citizenships.some((c) => EU_EEA.has(c));
  const hasRegister = (code: string) => registerCountries.size === 0 || registerCountries.has(code);
  const maxVisa = Math.max(1, ...countries.map((c) => demandFor(market, c.code, fams, hasRegister(c.code)).reachable));
  const weight = (p: Answers["priorities"][number]) => (answers.priorities.includes(p) ? 1.6 : 1);

  return countries
    .filter((c) => c.code !== answers.livesIn || answers.targets.includes(c.code))
    .map((c) => {
      const reasons: Reason[] = [];
      const add = (delta: number, text: L10n) => {
        if (delta) reasons.push({ delta: Math.round(delta), text });
      };
      const citizen = answers.citizenships.includes(c.code);
      const freeMovement = citizen || (euCitizen && (c.bloc === "eu" || c.bloc === "ch"));

      if (citizen) add(60, L("You're a citizen: no visa needed.", "Você é cidadão: não precisa de visto."));
      else if (freeMovement)
        add(50, L("Your EU/EEA citizenship lets you work here without a visa.", "Sua cidadania da UE/EEE permite trabalhar aqui sem visto."));
      else add(c.openness * 6 * weight("visa"), L(`Visa openness ${c.openness}/5: ${c.opennessNote.en}`, `Abertura a vistos ${c.openness}/5: ${c.opennessNote.pt}`));

      const demand = demandFor(market, c.code, fams, hasRegister(c.code));
      const dScore = (Math.log10(1 + demand.reachable) / Math.log10(1 + maxVisa)) * 25;
      if (hasRegister(c.code))
        add(dScore, L(
          `${demand.visaFriendly} open roles in your field with a visa signal (${demand.jobs} tracked in total).`,
          `${demand.visaFriendly} vagas abertas na sua área com sinal de visto (${demand.jobs} monitoradas no total).`,
        ));
      else
        add(dScore, L(
          `${demand.englishOk} open roles in your field in English (${demand.visaFriendly} say they sponsor). Any employer here can file a work permit, so many of the rest are possible too.`,
          `${demand.englishOk} vagas abertas na sua área em inglês (${demand.visaFriendly} dizem patrocinar). Qualquer empregador daqui pode pedir a autorização de trabalho, então muitas das outras também são possíveis.`,
        ));

      let languageGap = false;
      if (c.language && !speaks(profile, c.language.code)) {
        languageGap = c.language.importance !== "low";
        const base = { high: 18, medium: 9, low: 2 }[c.language.importance];
        const softened = answers.learnLanguage === "yes" ? 0.5 : answers.learnLanguage === "maybe" ? 0.75 : 1;
        add(-base * softened * weight("english"), L(
          `${c.language.name.en} matters for ${c.language.importance === "high" ? "many" : "some"} jobs here and your CV doesn't show it.`,
          `${c.language.name.pt} pesa em ${c.language.importance === "high" ? "muitas" : "algumas"} vagas aqui e seu CV não mostra esse idioma.`,
        ));
      } else if (c.language && speaks(profile, c.language.code)) {
        add(8, L(`You already speak ${c.language.name.en}.`, `Você já fala ${c.language.name.pt}.`));
      }
      if (c.englishWorkplace === "high") add(4 * weight("english"), L("English is widely used at work.", "O inglês é muito usado no trabalho."));

      if (!freeMovement && profile.degree === "none" && c.routes.length && c.routes.every((r) => r.degree === "required"))
        add(-15, L("The main work visas here require a university degree.", "Os principais vistos de trabalho daqui exigem diploma universitário."));
      if (!freeMovement && profile.degree === "none" && c.routes.some((r) => r.degree === "or-experience"))
        add(3, L("A route here accepts experience instead of a degree.", "Uma rota daqui aceita experiência no lugar do diploma."));

      if (answers.priorities.includes("residence") && /\b(1|2|21|3|three|two|one)\b.{0,12}(year|month)/i.test(c.residencePath.en))
        add(6, L(`Fast path to residence: ${c.residencePath.en}`, `Caminho rápido para residência: ${c.residencePath.pt}`));

      if (answers.targets.includes(c.code)) add(15, L("You chose this country.", "Você escolheu este país."));

      const score = reasons.reduce((s, r) => s + r.delta, 0);
      return { country: c, score, reasons: reasons.sort((a, b) => Math.abs(b.delta) - Math.abs(a.delta)), freeMovement, demand, languageGap };
    })
    .sort((a, b) => b.score - a.score);
}
