import { useRef, useState } from "react";
import { useT } from "../i18n";
import { parseCv } from "../cv/parse";
import { SKILLS } from "../data";
import type { Profile } from "../types";
import { Barcode, FlightArc, Plane } from "./Icons";

export default function Upload({ onRead }: { onRead: (text: string, profile: Profile) => void }) {
  const { t } = useT();
  const input = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [paste, setPaste] = useState("");
  const [over, setOver] = useState(false);

  const finish = (text: string) => {
    if (text.replace(/\s+/g, " ").trim().length < 200) {
      setError(t("cvTooShort"));
      return;
    }
    onRead(text, parseCv(text, SKILLS));
  };

  const readFile = async (file: File) => {
    setError("");
    setBusy(true);
    try {
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        const { pdfToText } = await import("../cv/pdf");
        finish(await pdfToText(file));
      } else {
        finish(await file.text());
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="hero">
      <FlightArc from="YOU" to="???" />
      <span className="eyebrow">{t("heroEyebrow")}</span>
      <h1>{t("heroTitle")}</h1>
      <p className="lede">{t("tagline")}</p>

      <div
        className={"ticket pass" + (over ? " over" : "")}
        role="button"
        tabIndex={0}
        aria-label={t("dropCv")}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setOver(false);
          const f = e.dataTransfer.files[0];
          if (f) readFile(f);
        }}
      >
        <div className="main-part">
          <div className="pass-head">
            <span>{t("passTitle")}</span>
            <span>VJA 2026</span>
          </div>
          <div className="fields">
            <div className="field"><b>{t("passenger")}</b><span>{t("yourCv")}</span></div>
            <div className="field"><b>{t("fromLbl")}</b><span>HOME</span></div>
            <div className="field"><b>{t("toLbl")}</b><span>{t("anywhere")}</span></div>
            <div className="field"><b>{t("classLbl")}</b><span>{t("classTech")}</span></div>
          </div>
          <div className="pass-cta">
            <Plane size={22} />
            <span>{busy ? t("reading") : t("dropCv")}</span>
          </div>
        </div>
        <div className="stub">
          <span className="label">{t("gateLbl")}</span>
          <span className="gate">PDF</span>
          <Barcode seed="VJA-CHECKIN" />
          <span className="label">{t("checkIn")}</span>
        </div>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf,.txt,.md"
          hidden
          onChange={(e) => e.target.files?.[0] && readFile(e.target.files[0])}
        />
      </div>

      <p className="privacy">🔒 {t("privacy")}</p>
      <details className="paste">
        <summary>{t("orPaste")}</summary>
        <textarea id="cv-paste" value={paste} onChange={(e) => setPaste(e.target.value)} rows={10} />
        <button className="btn primary" disabled={!paste.trim()} onClick={() => finish(paste)}>
          {t("readCv")}
        </button>
      </details>
      {error && <p className="error" role="alert">{error}</p>}
    </section>
  );
}
