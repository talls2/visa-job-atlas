import { useMemo, useRef, useState } from "react";
import { countryName, languageName, useT, type StringKey } from "../i18n";
import { COUNTRIES, KNOWLEDGE_AS_OF, TRACK, skillLabel, type Dataset } from "../data";
import { rankCountries, type CountryFit } from "../engine/countries";
import { matchJobs, type JobMatch } from "../engine/jobs";
import { buildPlan, type ItemKind, type Plan } from "../engine/plan";
import { MODELS, writePlanWithClaude } from "../engine/claude";
import { download, planToMarkdown } from "../export";
import { load, save } from "../store";
import { flightNo, hub, money } from "../travel";
import type { Answers, Lang, Market, Profile, Route } from "../types";
import Markdown from "./Markdown";
import { Barcode, Plane } from "./Icons";

type Tab = "overview" | "countries" | "jobs" | "plan" | "claude";
const EMPTY_MARKET: Market = { generatedAt: "", cells: {} };

export default function Results(props: { cvText: string; profile: Profile; answers: Answers; data: Dataset | null; dataError: string; onBack: () => void }) {
  const { t, lang } = useT();
  const [tab, setTab] = useState<Tab>("overview");
  const [claudeText, setClaudeText] = useState("");
  const market = props.data?.market ?? EMPTY_MARKET;
  const track = TRACK.get(props.answers.family)!;

  const registers = useMemo(() => new Set((props.data?.meta.registers ?? []).map((r) => r.country).filter(Boolean)), [props.data]);
  const fits = useMemo(() => rankCountries(COUNTRIES, market, props.profile, props.answers, registers), [market, props.profile, props.answers, registers]);
  const matches = useMemo(
    () => (props.data ? matchJobs(props.data.jobs, props.profile, props.answers, fits.map((f) => f.country.code), registers) : []),
    [props.data, props.profile, props.answers, fits, registers],
  );
  const plan = useMemo(() => buildPlan(track, fits, market, props.profile, props.answers, skillLabel), [track, fits, market, props.profile, props.answers]);
  const origin = props.answers.livesIn ? hub(props.answers.livesIn) : "HOME";

  const tabs: [Tab, StringKey][] = [["overview", "tabOverview"], ["countries", "tabCountries"], ["jobs", "tabJobs"], ["plan", "tabPlan"], ["claude", "tabClaude"]];
  return (
    <section>
      {!props.data && !props.dataError && <p className="note">{t("loadingData")}</p>}
      {props.dataError && <p className="error">{t("dataError")}</p>}
      <nav className="tabs" role="tablist">
        {tabs.map(([id, k]) => (
          <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}>{t(k)}</button>
        ))}
      </nav>
      {tab === "overview" && <Overview plan={plan} fits={fits} matches={matches} origin={origin} onTab={setTab} />}
      {tab === "countries" && <Countries fits={fits} origin={origin} />}
      {tab === "jobs" && <Jobs matches={matches} fits={fits} />}
      {tab === "plan" && <PlanView plan={plan} />}
      {tab === "claude" && (
        <Claude cvText={props.cvText} profile={props.profile} answers={props.answers} plan={plan} matches={matches} text={claudeText} setText={setClaudeText} />
      )}
      <div className="nav">
        <button className="btn ghost" onClick={props.onBack}>{t("back")}</button>
        <div className="row">
          <button className="btn" onClick={() => download(`visa-job-atlas-plan-${lang}.md`, planToMarkdown(plan, matches, lang, claudeText))}>{t("download")}</button>
          <button className="btn" onClick={() => window.print()}>{t("print")}</button>
        </div>
      </div>
      <p className="muted small">{t("knowledgeAsOf")}: {KNOWLEDGE_AS_OF}</p>
    </section>
  );
}

function floorText(r: Route | undefined, lang: Lang, t: (k: StringKey) => string) {
  if (!r?.salaryMin) return null;
  const per = r.salaryMin.period.startsWith("month") ? t("perMonth") : r.salaryMin.period.startsWith("year") ? t("perYear") : `/${r.salaryMin.period}`;
  return <span className="fare">{money(r.salaryMin.amount, r.salaryMin.currency, lang)}<small>{per}</small></span>;
}

function Overview({ plan, fits, matches, origin, onTab }: { plan: Plan; fits: CountryFit[]; matches: JobMatch[]; origin: string; onTab: (t: Tab) => void }) {
  const { t, tx, lang } = useT();
  const best = fits[0];
  const thisWeek = plan.phases[0].items.slice(0, 5);
  const firstRoute = best && !best.freeMovement ? best.country.routes[0] : undefined;
  return (
    <div className="overview">
      <div className="board" role="region" aria-label={t("departures")}>
        <div className="board-title">
          <span>{t("departures")}</span>
          <Plane className="plane" size={22} />
        </div>
        <div className="deps">
          {fits.slice(0, 6).map((f, i) => {
            const route = f.freeMovement ? "EU free movement" : tx(f.country.routes[0]?.name ?? null);
            return (
              <button key={f.country.code} className="dep" onClick={() => onTab("countries")}>
                <span className="dcode">{hub(f.country.code)}</span>
                <span>
                  <span className="dname">{countryName(f.country.code, lang)}</span>
                  <span className="droute">{route}</span>
                </span>
                <span className="droles"><b>{f.freeMovement ? f.demand.jobs : f.demand.reachable}</b>{t("rolesLbl")}</span>
                <span className={"st " + (f.freeMovement ? "go" : i === 0 ? "now" : "visa")}>
                  {f.freeMovement ? t("stNoVisa") : i === 0 ? t("stBoarding") : t("stVisa")}
                </span>
              </button>
            );
          })}
        </div>
        <p className="board-foot">{t("boardNote")}</p>
      </div>

      {best && (
        <div className="ticket lead-pass">
          <div className="main-part">
            <div className="pass-head"><span>{t("overviewLead")}</span><span>{flightNo(best.country.code)}</span></div>
            <div className="trip">
              <span>{origin}<small>{t("fromLbl")}</small></span>
              <span className="dash"><Plane className="plane" size={22} /></span>
              <span>{hub(best.country.code)}<small>{tx(best.country.name)}</small></span>
            </div>
            <ul>{best.reasons.slice(0, 4).map((r, i) => <li key={i}>{tx(r.text)}</li>)}</ul>
            {firstRoute && <p><b>{tx(firstRoute.name)}</b>: {tx(firstRoute.summary)}</p>}
          </div>
          <div className="stub">
            <span className="label">{t("salaryFloor")}</span>
            {floorText(firstRoute, lang, t) ?? <span className="stamp good">{best.freeMovement ? t("stNoVisa") : "—"}</span>}
            <span className="label">{t("rolesLbl")}</span>
            <span className="fare" style={{ color: "var(--navy)" }}>{best.freeMovement ? best.demand.jobs : best.demand.reachable}</span>
            <Barcode seed={best.country.code + origin} />
          </div>
        </div>
      )}

      <div className="grid2">
        <div className="card">
          <h3>{t("thisWeek")}</h3>
          <ol>{thisWeek.map((it, i) => <li key={i}>{tx(it.text)}</li>)}</ol>
          <button className="btn small" onClick={() => onTab("jobs")}>{matches.length} {t("matches")} →</button>
        </div>
        <div className="card">
          <h3>{t("firstRoles")}</h3>
          <p>{tx(plan.track.firstSponsoredRoles)}</p>
          {plan.gaps.length > 0 && (
            <>
              <h3>{t("gaps")}</h3>
              <div className="chips">{plan.gaps.slice(0, 6).map((g) => <span key={g.id} className="chip">{skillLabel(g.id)}</span>)}</div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function Countries({ fits, origin }: { fits: CountryFit[]; origin: string }) {
  const { t, tx, lang } = useT();
  return (
    <div className="countries">
      {fits.map((f, i) => {
        const r0 = f.country.routes[0];
        return (
          <details key={f.country.code} className="ticket country" open={i === 0}>
            <summary>
              <span className="main-part head">
                <span className="code">{hub(f.country.code)}</span>
                <span>
                  <span className="cname">{tx(f.country.name)}</span>
                  <span className="meta">{" · "}{origin} → {hub(f.country.code)}{" · "}{flightNo(f.country.code, i)}</span>
                  <br />
                  {f.freeMovement ? <span className="stamp good">{t("noVisa")}</span> : r0 && <span className="meta">{tx(r0.name)} {floorText(r0, lang, t)}</span>}
                </span>
                <span className="chev" aria-hidden="true">›</span>
              </span>
              <span className="stub">
                <span className="rank">{t("rankLbl")} #{i + 1}</span>
                <span className="score">{f.score}</span>
                <span className="label">{t("fitLbl")}</span>
              </span>
            </summary>
            <div className="main-part" style={{ paddingTop: 0 }}>
              <div className="country-body">
                <div>
                  <h4>{t("whyThis")}</h4>
                  <ul className="reasons">
                    {f.reasons.map((r, j) => (
                      <li key={j} className={r.delta >= 0 ? "pos" : "neg"}><span className="num">{r.delta > 0 ? "+" : ""}{r.delta}</span> {tx(r.text)}</li>
                    ))}
                  </ul>
                  {f.country.catches.length > 0 && (<><h4>{t("catches")}</h4><ul>{f.country.catches.map((c, j) => <li key={j}>{tx(c)}</li>)}</ul></>)}
                  {f.country.recentChanges.length > 0 && (<><h4>{t("recent")}</h4><ul>{f.country.recentChanges.map((c, j) => <li key={j}>{tx(c)}</li>)}</ul></>)}
                </div>
                <div>
                  <h4>{t("routes")}</h4>
                  {f.country.routes.map((r) => (
                    <div key={r.id} className="route-item">
                      <div className="route-top"><b>{tx(r.name)}</b>{floorText(r, lang, t)}</div>
                      <p>{tx(r.summary)}</p>
                      <p className="muted small">
                        {r.degree === "required" ? t("degreeReq") : r.degree === "or-experience" ? t("degreeOrExp") : t("degreeNo")}.{" "}
                        {r.processing && tx(r.processing)}{" "}
                        {r.source && <a href={r.source} target="_blank" rel="noopener">{t("sources")}</a>}
                      </p>
                    </div>
                  ))}
                  <h4>{t("residence")}</h4>
                  <p>{tx(f.country.residencePath)}</p>
                  {f.country.language && (<><h4>{t("languagePlan")}: {tx(f.country.language.name)}</h4><p>{tx(f.country.language.note)}</p></>)}
                  <h4>{t("cvTips")}</h4>
                  <p>{tx(f.country.cvTips)}</p>
                  {f.country.jobBoards.length > 0 && (
                    <p><b>{t("jobBoards")}:</b> {f.country.jobBoards.map((b, j) => <span key={b.url}>{j > 0 && " · "}<a href={b.url} target="_blank" rel="noopener">{b.name}</a></span>)}</p>
                  )}
                  {f.country.sponsorRegister && <p><a href={f.country.sponsorRegister.url} target="_blank" rel="noopener">{t("sponsorReg")}: {tx(f.country.sponsorRegister.name)}</a></p>}
                </div>
              </div>
            </div>
          </details>
        );
      })}
    </div>
  );
}

function Jobs({ matches, fits }: { matches: JobMatch[]; fits: CountryFit[] }) {
  const { t, lang } = useT();
  const [country, setCountry] = useState("");
  const [showBlocked, setShowBlocked] = useState(false);
  const [limit, setLimit] = useState(40);
  const shown = matches.filter((m) => (showBlocked || !m.languageBlock.length) && (!country || m.job.countries.includes(country)));
  return (
    <div>
      <div className="filters row">
        <label>
          {t("filterCountry")}{" "}
          <select id="job-country" value={country} onChange={(e) => setCountry(e.target.value)}>
            <option value="">{t("allCountries")}</option>
            {fits.slice(0, 8).map((f) => <option key={f.country.code} value={f.country.code}>{hub(f.country.code)} · {countryName(f.country.code, lang)}</option>)}
          </select>
        </label>
        <label className="check"><input type="checkbox" checked={showBlocked} onChange={(e) => setShowBlocked(e.target.checked)} /> {t("showLangBlocked")}</label>
      </div>
      <p className="muted"><b className="mono">{shown.length}</b> {t("matches")}</p>
      <div className="joblist">
        {shown.slice(0, limit).map((m) => {
          const good = m.noVisaNeeded || ["explicit", "register", "employer-yes"].includes(m.job.visa);
          const stampCls = good ? "good" : m.openMarket || m.job.visa === "conditional" || m.job.visa === "relocation" ? "warn" : "plain";
          const where = m.job.countries.length ? m.job.countries.map(hub).join(" · ") : "REMOTE";
          return (
            <article key={m.job.id} className="ticket job">
              <div className="main-part">
                <a className="job-title" href={m.job.url} target="_blank" rel="noopener">{m.job.title}</a>
                <p className="muted">{m.job.company}{" · "}{m.job.location || m.job.countries.map((c) => countryName(c, lang)).join(", ")}</p>
                <div className="chips">
                  <span className={"stamp " + stampCls}>
                    {m.noVisaNeeded ? t("noVisa") : m.openMarket ? t("visa_open") : t(("visa_" + m.job.visa) as StringKey)}
                  </span>
                  {m.languageBlock.map((l) => <span key={l} className="badge bad">{languageName(l, lang)}</span>)}
                  {m.matchedSkills.slice(0, 5).map((s) => <span key={s} className="chip have">{skillLabel(s)}</span>)}
                  {m.missingSkills.slice(0, 3).map((s) => <span key={s} className="chip miss">{skillLabel(s)}</span>)}
                </div>
                {(m.job.posted || m.job.salary) && (
                  <p className="muted small">
                    {m.job.posted && <>{t("posted")}: <span className="mono">{m.job.posted}</span></>}
                    {m.job.salary && <> · <span className="fare">{m.job.salary}</span></>}
                  </p>
                )}
              </div>
              <div className="stub">
                <span className="lbl">{t("toLbl")}</span>
                <span className="seat" title={where}>{where.length > 7 ? where.slice(0, 3) + "+" : where}</span>
                <span className="lbl">{t("fitLbl")} <b className="mono">{m.score}</b></span>
              </div>
            </article>
          );
        })}
      </div>
      {shown.length > limit && <button className="btn" onClick={() => setLimit(limit + 40)}>+40</button>}
    </div>
  );
}

const KIND: Record<ItemKind, string> = {
  profile: "ID", skill: "SK", cert: "CRT", project: "PRJ", language: "LNG", network: "NET", apply: "APP", visa: "VSA",
};

function PlanView({ plan }: { plan: Plan }) {
  const { t, tx } = useT();
  return (
    <div className="plan">
      {plan.switchTip && <div className="card" style={{ marginBottom: 16 }}><h3>{t("switchTip")}</h3><p>{tx(plan.switchTip)}</p></div>}
      <div className="itinerary">
        {plan.phases.map((ph, i) => (
          <div key={ph.id} className="legrow">
            <div className="rail"><span className="dot">{i + 1}</span><span className="line" /></div>
            <div className="card leg-card">
              <div className="leg-head">
                <h3>{tx(ph.title)}</h3>
                <span className="flight">{t("legLbl")} {i + 1} · {flightNo(plan.track.id.slice(0, 2).toUpperCase(), i)}</span>
              </div>
              <ul className="items">
                {ph.items.map((it, j) => (
                  <li key={j}>
                    <span className="kind" aria-hidden="true">{KIND[it.kind]}</span>
                    <div>
                      <b>{tx(it.text)}</b>
                      {it.detail && <p className="muted small">{tx(it.detail)}</p>}
                      {it.url && <a className="small" href={it.url} target="_blank" rel="noopener">{it.url.replace(/^https?:\/\//, "").slice(0, 50)}</a>}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
      <div className="grid2">
        <div className="card">
          <h3>{t("certsToGet")}</h3>
          <ul>{plan.certs.map((c) => <li key={c.name}><a href={c.url} target="_blank" rel="noopener">{c.name}</a> ({c.provider}, <span className="fare">{c.cost}</span>): {tx(c.why)}</li>)}</ul>
          <h3>{t("weekly")}</h3>
          <ul>{plan.weekly.map((w, i) => <li key={i}>{tx(w)}</li>)}</ul>
        </div>
        <div className="card">
          {plan.gaps.length > 0 && (
            <>
              <h3>{t("gaps")}</h3>
              <ul>{plan.gaps.map((g) => <li key={g.id}>{skillLabel(g.id)} <span className="muted mono small">({g.count} {t("inPostings")})</span></li>)}</ul>
            </>
          )}
          <h3>{t("connectionNote")}</h3>
          <blockquote>{tx(plan.connectionNote)}</blockquote>
        </div>
      </div>
    </div>
  );
}

function Claude(props: { cvText: string; profile: Profile; answers: Answers; plan: Plan; matches: JobMatch[]; text: string; setText: (s: string) => void }) {
  const { t, lang } = useT();
  const [remember, setRemember] = useState(() => !!load("vja.key", ""));
  const [key, setKey] = useState<string>(() => load("vja.key", "") || load("vja.key", "", true));
  const [model, setModel] = useState(MODELS[0].id);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const abort = useRef<AbortController | null>(null);

  const run = async () => {
    save("vja.key", remember ? key : null);
    save("vja.key", key, true);
    setBusy(true);
    setError("");
    props.setText("");
    abort.current = new AbortController();
    let acc = "";
    try {
      const { stopReason } = await writePlanWithClaude(
        key.trim(), model,
        { cvText: props.cvText, profile: props.profile, answers: props.answers, plan: props.plan, matches: props.matches, lang },
        (chunk) => { acc += chunk; props.setText(acc); },
        abort.current.signal,
      );
      if (stopReason === "refusal") setError(t("refused"));
    } catch (e) {
      if (!abort.current.signal.aborted) setError(`${t("claudeError")}: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="claude">
      <p>{t("claudeIntro")}</p>
      <div className="row wrap-row">
        <label className="grow">
          {t("apiKey")} (<a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener">{t("getKey")}</a>)
          <input id="claude-key" type="password" autoComplete="off" spellCheck={false} value={key} onChange={(e) => setKey(e.target.value)} placeholder="sk-ant-…" />
        </label>
        <label>
          {t("model")}
          <select id="claude-model" value={model} onChange={(e) => setModel(e.target.value)}>
            {MODELS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
        </label>
      </div>
      <label className="check"><input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} /> {t("rememberKey")}</label>
      <div className="row">
        <button className="btn primary" disabled={!key.trim() || busy} onClick={run}>{t("writePlan")}</button>
        {busy && <button className="btn ghost" onClick={() => abort.current?.abort()}>{t("stop")}</button>}
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      {props.text && <div className="card prose"><Markdown text={props.text} /></div>}
    </div>
  );
}
