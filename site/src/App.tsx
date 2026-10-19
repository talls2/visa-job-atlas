import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import { LangContext, useT } from "./i18n";
import type { Answers, Lang, Profile } from "./types";
import { loadDataset, type Dataset } from "./data";
import { load, save } from "./store";
import Upload from "./components/Upload";
import Review from "./components/Review";
import Interview, { defaultAnswers } from "./components/Interview";
import Results from "./components/Results";
import { Plane } from "./components/Icons";

type Step = "upload" | "review" | "interview" | "results";
const STEPS: Step[] = ["upload", "review", "interview", "results"];

export default function App() {
  const [lang, setLang] = useState<Lang>(() =>
    load<Lang>("vja.lang", navigator.language?.toLowerCase().startsWith("pt") ? "pt" : "en"),
  );
  const [step, setStep] = useState<Step>(() => load<Step>("vja.step", "upload", true));
  const [cvText, setCvText] = useState<string>(() => load("vja.cv", "", true));
  const [profile, setProfile] = useState<Profile | null>(() => load<Profile | null>("vja.profile", null, true));
  const [answers, setAnswers] = useState<Answers | null>(() => load<Answers | null>("vja.answers", null, true));
  const [data, setData] = useState<Dataset | null>(null);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    loadDataset().then(setData, (e) => setDataError(String(e)));
  }, []);
  useEffect(() => save("vja.lang", lang), [lang]);
  useEffect(() => save("vja.step", step, true), [step]);
  useEffect(() => save("vja.cv", cvText, true), [cvText]);
  useEffect(() => save("vja.profile", profile, true), [profile]);
  useEffect(() => save("vja.answers", answers, true), [answers]);
  useEffect(() => {
    document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
    window.scrollTo({ top: 0 });
  }, [lang, step]);

  const reset = () => {
    setCvText("");
    setProfile(null);
    setAnswers(null);
    setStep("upload");
  };
  const current = profile ? step : "upload";
  const idx = STEPS.indexOf(current);
  const effectiveAnswers = useMemo(() => (profile ? answers ?? defaultAnswers(profile) : null), [answers, profile]);

  return (
    <LangContext.Provider value={lang}>
      <Shell lang={lang} setLang={setLang} idx={idx} onReset={profile ? reset : undefined} dataAsOf={data?.meta.generatedAt}>
        {current === "upload" && (
          <Upload
            onRead={(text, p) => {
              setCvText(text);
              setProfile(p);
              setAnswers(null);
              setStep("review");
            }}
          />
        )}
        {current === "review" && profile && (
          <Review profile={profile} onChange={setProfile} onBack={reset} onNext={() => setStep("interview")} />
        )}
        {current === "interview" && profile && effectiveAnswers && (
          <Interview
            profile={profile}
            answers={effectiveAnswers}
            onChange={setAnswers}
            onBack={() => setStep("review")}
            onNext={() => {
              setAnswers(effectiveAnswers);
              setStep("results");
            }}
          />
        )}
        {current === "results" && profile && effectiveAnswers && (
          <Results
            cvText={cvText}
            profile={profile}
            answers={effectiveAnswers}
            data={data}
            dataError={dataError}
            onBack={() => setStep("interview")}
          />
        )}
      </Shell>
    </LangContext.Provider>
  );
}

function Shell(props: {
  lang: Lang;
  setLang: (l: Lang) => void;
  idx: number;
  onReset?: () => void;
  dataAsOf?: string;
  children: ReactNode;
}) {
  const { t } = useT();
  const labels = [t("stepUpload"), t("stepReview"), t("stepInterview"), t("stepResults")];
  const codes = ["CV", "PRF", "QST", "PLN"];
  return (
    <>
      <header className="top">
        <div className="wrap top-in">
          <div className="brand">
            <Plane className="plane" size={22} />
            <span>{t("appName")}</span>
          </div>
          <ol className="route" aria-label="Progress">
            {labels.map((l, i) => (
              <Fragment key={l}>
                {i > 0 && (
                  <li className={"leg" + (i <= props.idx ? " flown" : "")} aria-hidden="true">
                    {i === props.idx && <Plane className="plane" size={20} />}
                  </li>
                )}
                <li className={i === props.idx ? "on" : i < props.idx ? "done" : ""} aria-current={i === props.idx ? "step" : undefined}>
                  <span className="code">{codes[i]}</span> <span className="name">{l}</span>
                </li>
              </Fragment>
            ))}
          </ol>
          <div className="top-actions">
            {props.onReset && (
              <button className="btn ghost small" onClick={props.onReset}>
                {t("startOver")}
              </button>
            )}
            <div className="lang" role="group" aria-label="Language">
              {(["en", "pt"] as Lang[]).map((l) => (
                <button key={l} aria-pressed={props.lang === l} onClick={() => props.setLang(l)}>
                  {l === "en" ? "EN" : "PT"}
                </button>
              ))}
            </div>
          </div>
        </div>
      </header>
      <main className="wrap main">{props.children}</main>
      <footer className="wrap foot">
        <p><b>{t("safeTravels")}</b> {t("disclaimer")}</p>
        <p className="muted">
          {t("footer")}{" "}
          {props.dataAsOf && (
            <>
              {t("dataAsOf")}: {props.dataAsOf.slice(0, 10)}.
            </>
          )}{" "}
          <a href="https://github.com/talls2/visa-job-atlas" rel="noopener">GitHub</a>
        </p>
      </footer>
    </>
  );
}
