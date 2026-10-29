import { useMemo } from "react";
import { countryName, useT, type StringKey } from "../i18n";
import { COUNTRIES, TRACK, TRACKS } from "../data";
import { REGIONS } from "../regions";
import { hub } from "../travel";
import type { Answers, Family, Priority, Profile } from "../types";

export function defaultAnswers(profile: Profile): Answers {
  return {
    citizenships: [],
    livesIn: "",
    targets: [],
    priorities: ["visa"],
    direction: "stay",
    family: profile.families[0] ?? "software",
    niche: "",
    learnLanguage: "maybe",
    hoursPerWeek: 8,
    budget: "low",
    horizon: 12,
    withFamily: false,
  };
}

// Fields grouped for the picker; a track missing from knowledge/tracks.json is skipped.
const GROUPS: [StringKey, Family[]][] = [
  ["groupTech", ["software", "data", "devops", "security", "embedded", "qa", "product"]],
  ["groupCreative", ["design", "video"]],
  ["groupEngineering", ["mechanical", "electrical", "civil"]],
  ["groupBusiness", ["marketing", "sales", "finance", "operations", "people"]],
  ["groupHealth", ["healthcare"]],
];

const PRIORITIES: [Priority, StringKey][] = [
  ["visa", "prVisa"], ["english", "prEnglish"], ["salary", "prSalary"], ["residence", "prResidence"], ["quality", "prQuality"],
];

function Choice<T extends string | number>(props: { value: T; options: [T, string][]; onChange: (v: T) => void; name: string }) {
  return (
    <div className="choices" role="radiogroup" aria-label={props.name}>
      {props.options.map(([v, label]) => (
        <button key={String(v)} role="radio" aria-checked={props.value === v} className={"choice" + (props.value === v ? " on" : "")} onClick={() => props.onChange(v)}>
          {label}
        </button>
      ))}
    </div>
  );
}

export default function Interview(props: { profile: Profile; answers: Answers; onChange: (a: Answers) => void; onBack: () => void; onNext: () => void }) {
  const { t, tx, lang } = useT();
  const a = props.answers;
  const set = (patch: Partial<Answers>) => props.onChange({ ...a, ...patch });
  const regions = useMemo(
    () => REGIONS.map((c) => [c, countryName(c, lang)] as const).sort((x, y) => x[1].localeCompare(y[1], lang)),
    [lang],
  );
  const covered = useMemo(
    () => COUNTRIES.map((c) => [c.code, tx(c.name)] as const).sort((x, y) => x[1].localeCompare(y[1], lang)),
    [lang, tx],
  );
  const toggle = <T,>(list: T[], v: T, max = 99) => (list.includes(v) ? list.filter((x) => x !== v) : list.length >= max ? list : [...list, v]);
  const track = TRACK.get(a.family);

  return (
    <section className="interview">
      <div className="q">
        <h3>{t("qCitizenship")}</h3>
        <p className="help">{t("qCitizenshipHelp")}</p>
        <div className="chips">
          {a.citizenships.map((c) => (
            <button key={c} className="chip removable" onClick={() => set({ citizenships: a.citizenships.filter((x) => x !== c) })}>
              {countryName(c, lang)} <span aria-hidden="true">×</span>
            </button>
          ))}
          <select value="" onChange={(e) => e.target.value && set({ citizenships: toggle(a.citizenships, e.target.value) })} aria-label={t("qCitizenship")}>
            <option value="">+</option>
            {regions.filter(([c]) => !a.citizenships.includes(c)).map(([c, n]) => <option key={c} value={c}>{n}</option>)}
          </select>
        </div>
      </div>

      <div className="q">
        <h3>{t("qLivesIn")}</h3>
        <select value={a.livesIn} onChange={(e) => set({ livesIn: e.target.value })} aria-label={t("qLivesIn")}>
          <option value="">—</option>
          {regions.map(([c, n]) => <option key={c} value={c}>{n}</option>)}
        </select>
      </div>

      <div className="q">
        <h3>{t("qTargets")}</h3>
        <p className="help">{t("qTargetsHelp")}</p>
        <div className="chips">
          {covered.map(([c, n]) => (
            <button key={c} className={"chip toggle" + (a.targets.includes(c) ? " on" : "")} aria-pressed={a.targets.includes(c)} onClick={() => set({ targets: toggle(a.targets, c, 5) })}>
              <span className="dest"><span className="mono">{hub(c)}</span>{n}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="q">
        <h3>{t("qPriorities")}</h3>
        <div className="chips">
          {PRIORITIES.map(([p, k]) => (
            <button key={p} className={"chip toggle" + (a.priorities.includes(p) ? " on" : "")} aria-pressed={a.priorities.includes(p)} onClick={() => set({ priorities: toggle(a.priorities, p, 2) })}>
              {t(k)}
            </button>
          ))}
        </div>
      </div>

      <div className="q">
        <h3>{t("qDirection")}</h3>
        <Choice name={t("qDirection")} value={a.direction} onChange={(direction) => set({ direction, family: direction === "stay" ? props.profile.families[0] ?? a.family : a.family })}
          options={[["stay", t("dirStay")], ["switch", t("dirSwitch")], ["unsure", t("dirUnsure")]]} />
      </div>

      <div className="q">
        <h3>{t("qFamily")}</h3>
        {GROUPS.map(([label, ids]) => {
          const group = ids.map((id) => TRACKS.find((tr) => tr.id === id)).filter((tr) => tr !== undefined);
          if (!group.length) return null;
          return (
            <div key={label} className="track-group">
              <h4>{t(label)}</h4>
              <div className="tracks">
                {group.map((tr) => (
                  <button key={tr.id} className={"track" + (a.family === tr.id ? " on" : "")} aria-pressed={a.family === tr.id} onClick={() => set({ family: tr.id as Family, niche: "" })}>
                    <b>{tx(tr.name)}</b>
                    {a.family === tr.id && <span>{tx(tr.summary)}</span>}
                    {props.profile.families[0] === tr.id && <em className="tag">{t("detectedField")}</em>}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
        {track && track.niches.length > 0 && (
          <label className="niche">
            {t("qNiche")}
            <select value={a.niche} onChange={(e) => set({ niche: e.target.value })}>
              <option value="">{t("anyNiche")}</option>
              {track.niches.map((n) => <option key={n.id} value={n.id}>{tx(n.name)}</option>)}
            </select>
          </label>
        )}
      </div>

      <div className="grid2">
        <div className="q">
          <h3>{t("qLearnLang")}</h3>
          <Choice name={t("qLearnLang")} value={a.learnLanguage} onChange={(learnLanguage) => set({ learnLanguage })} options={[["yes", t("yes")], ["maybe", t("maybe")], ["no", t("no")]]} />
        </div>
        <div className="q">
          <h3>{t("qHorizon")}</h3>
          <Choice name={t("qHorizon")} value={a.horizon} onChange={(horizon) => set({ horizon })} options={[[6, t("h6")], [12, t("h12")], [24, t("h24")]]} />
        </div>
        <div className="q">
          <h3>{t("qHours")}: {a.hoursPerWeek}h</h3>
          <input type="range" min={2} max={30} value={a.hoursPerWeek} onChange={(e) => set({ hoursPerWeek: Number(e.target.value) })} aria-label={t("qHours")} />
        </div>
        <div className="q">
          <h3>{t("qBudget")}</h3>
          <select value={a.budget} onChange={(e) => set({ budget: e.target.value as Answers["budget"] })} aria-label={t("qBudget")}>
            <option value="none">{t("bNone")}</option>
            <option value="low">{t("bLow")}</option>
            <option value="medium">{t("bMedium")}</option>
            <option value="high">{t("bHigh")}</option>
          </select>
        </div>
      </div>
      <label className="check">
        <input type="checkbox" checked={a.withFamily} onChange={(e) => set({ withFamily: e.target.checked })} /> {t("qWithFamily")}
      </label>

      <div className="nav">
        <button className="btn ghost" onClick={props.onBack}>{t("back")}</button>
        <button className="btn primary" onClick={props.onNext}>{t("buildPlan")}</button>
      </div>
    </section>
  );
}
