import { useState } from "react";
import { languageName, useT, type StringKey } from "../i18n";
import { SKILLS, TRACK, skillLabel } from "../data";
import type { Degree, Level, Profile } from "../types";

const LEVELS: Level[] = ["entry", "junior", "mid", "senior", "lead"];
const DEGREES: Degree[] = ["none", "technical", "bachelor", "master", "phd"];
const LANG_LEVELS = ["basic", "intermediate", "fluent", "native"] as const;
const COMMON_LANGS = ["en", "pt", "es", "de", "fr", "it", "ja", "nl", "sv", "zh", "ko", "pl"];

export default function Review(props: { profile: Profile; onChange: (p: Profile) => void; onBack: () => void; onNext: () => void }) {
  const { t, tx, lang } = useT();
  const p = props.profile;
  const set = (patch: Partial<Profile>) => props.onChange({ ...p, ...patch });
  const [newSkill, setNewSkill] = useState("");
  const [newLang, setNewLang] = useState("");
  const unknown = SKILLS.filter((s) => !p.skills.includes(s.id)).sort((a, b) => a.label.localeCompare(b.label));

  return (
    <section>
      <h2>{t("reviewTitle")}</h2>
      <div className="grid2">
        <div className="card">
          <h3>{t("skills")}</h3>
          <div className="chips">
            {p.skills.map((id) => (
              <button key={id} className="chip removable" title={t("remove")} onClick={() => set({ skills: p.skills.filter((s) => s !== id) })}>
                {skillLabel(id)} <span aria-hidden="true">×</span>
              </button>
            ))}
          </div>
          <div className="row">
            <select value={newSkill} onChange={(e) => setNewSkill(e.target.value)} aria-label={t("addSkill")}>
              <option value="">{t("addSkill")}…</option>
              {unknown.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
            <button className="btn small" disabled={!newSkill} onClick={() => { set({ skills: [...p.skills, newSkill] }); setNewSkill(""); }}>+</button>
          </div>
        </div>

        <div className="card stack">
          <label>
            {t("years")}
            <input type="number" min={0} max={50} step={0.5} value={p.years} onChange={(e) => set({ years: Number(e.target.value) })} />
          </label>
          <label>
            {t("level")}
            <select value={p.level} onChange={(e) => set({ level: e.target.value as Level })}>
              {LEVELS.map((l) => <option key={l} value={l}>{t(("lvl_" + l) as StringKey)}</option>)}
            </select>
          </label>
          <label>
            {t("degree")}
            <select value={p.degree} onChange={(e) => set({ degree: e.target.value as Degree })}>
              {DEGREES.map((d) => <option key={d} value={d}>{t(("deg_" + d) as StringKey)}</option>)}
            </select>
          </label>
          <div>
            <span className="label">{t("detectedField")}</span>
            <p>{p.families.slice(0, 3).map((f) => tx(TRACK.get(f)?.name)).join(" · ")}</p>
          </div>
          {p.certs.length > 0 && (
            <div>
              <span className="label">{t("certs")}</span>
              <p>{p.certs.join(", ")}</p>
            </div>
          )}
          {p.titles.length > 0 && (
            <div>
              <span className="label">{t("titlesFound")}</span>
              <p className="muted small">{p.titles.slice(0, 5).join(" · ")}</p>
            </div>
          )}
        </div>

        <div className="card">
          <h3>{t("languages")}</h3>
          {p.languages.map((l, i) => (
            <div className="row" key={l.code}>
              <span className="grow">{languageName(l.code, lang)}</span>
              <select
                value={l.level}
                onChange={(e) => {
                  const languages = [...p.languages];
                  languages[i] = { ...l, level: e.target.value as typeof l.level };
                  set({ languages });
                }}
              >
                {LANG_LEVELS.map((v) => <option key={v} value={v}>{t(("ll_" + v) as StringKey)}</option>)}
              </select>
              <button className="btn ghost small" aria-label={t("remove")} onClick={() => set({ languages: p.languages.filter((x) => x.code !== l.code) })}>×</button>
            </div>
          ))}
          <div className="row">
            <select value={newLang} onChange={(e) => setNewLang(e.target.value)} aria-label={t("addLanguage")}>
              <option value="">{t("addLanguage")}…</option>
              {COMMON_LANGS.filter((c) => !p.languages.some((l) => l.code === c)).map((c) => (
                <option key={c} value={c}>{languageName(c, lang)}</option>
              ))}
            </select>
            <button className="btn small" disabled={!newLang} onClick={() => { set({ languages: [...p.languages, { code: newLang, level: "intermediate" }] }); setNewLang(""); }}>+</button>
          </div>
        </div>
      </div>
      <div className="nav">
        <button className="btn ghost" onClick={props.onBack}>{t("back")}</button>
        <button className="btn primary" onClick={props.onNext}>{t("next")}</button>
      </div>
    </section>
  );
}
