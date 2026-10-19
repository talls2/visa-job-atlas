"""Writes the web app's data files (see docs/DATA.md):

    site/public/data/jobs.json    open postings that don't rule sponsorship out
    site/public/data/market.json  demand per country and job family, with top skills
    site/public/data/meta.json    sources, registers and run time
"""

import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[2] / "site" / "public" / "data"

FIELDS = ["id", "title", "company", "location", "countries", "url", "posted", "firstSeen",
          "family", "seniority", "remote", "visa", "registerIn", "skills", "langs", "salary"]
HIDDEN = {"blocked", "employer-no"}  # postings that rule sponsorship out are not shown
VISA_FRIENDLY = {"explicit", "conditional", "register", "employer-yes", "relocation"}
MAX_AGE_DAYS = 120  # drop stale postings that boards forget to close


def _split(s):
    return [x for x in (s or "").split(",") if x]


def _trim(s, n):
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _iso(ts):
    return (ts or "").replace(" ", "T")[:19] + "Z" if ts else ""


def build(con, out_dir=OUT_DIR):
    out_dir.mkdir(parents=True, exist_ok=True)
    last = con.execute("SELECT MAX(run_at) FROM snapshots").fetchone()[0] or ""
    cutoff = (dt.date.today() - dt.timedelta(days=MAX_AGE_DAYS)).isoformat()

    rows, cells = [], defaultdict(lambda: {"jobs": 0, "visaFriendly": 0, "englishOk": 0, "skills": Counter()})
    for j in con.execute("SELECT * FROM jobs WHERE closed_at IS NULL ORDER BY first_seen DESC"):
        if j["label"] in HIDDEN or not j["family"]:
            continue
        if j["posted_at"] and j["posted_at"][:10] < cutoff:
            continue
        ctry, skills = _split(j["countries"]), _split(j["skills"])
        rows.append([
            j["uid"], _trim(j["title"], 140), _trim(j["company"], 60), _trim(j["location"], 90), ctry,
            j["url"] or "", (j["posted_at"] or "")[:10], (j["first_seen"] or "")[:10], j["family"],
            j["seniority"] or "unspecified", j["remote"] or 0, j["label"] or "unknown", _split(j["register_in"]),
            skills, _split(j["langs"]), _trim(j["salary"], 60),
        ])
        for c in ctry or ["REMOTE"]:
            cell = cells[f"{c}|{j['family']}"]
            cell["jobs"] += 1
            cell["visaFriendly"] += j["label"] in VISA_FRIENDLY
            cell["englishOk"] += not j["langs"]
            cell["skills"].update(skills)

    generated = _iso(last) or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    jobs = {"generatedAt": generated, "fields": FIELDS, "rows": rows}
    market = {"generatedAt": generated, "cells": {
        k: {"jobs": v["jobs"], "visaFriendly": v["visaFriendly"], "englishOk": v["englishOk"], "skills": dict(v["skills"].most_common(25))}
        for k, v in sorted(cells.items())}}
    sources = [{"name": r["company"], "kind": "feed" if r["company"].startswith("[feed]") else "board",
                "ok": bool(r["ok"]), "listed": r["total_open"], "kept": r["kept"], "error": _trim(r["error"], 160)}
               for r in con.execute("SELECT * FROM snapshots WHERE run_at = ? ORDER BY company", (last,))]
    country_of = {r["source"]: r["country"] for r in con.execute("SELECT source, MIN(country) country FROM sponsors GROUP BY source")}
    registers = [{"source": r["source"], "country": country_of.get(r["source"], ""), "rows": r["rows"],
                  "loadedAt": r["loaded_at"][:10]} for r in con.execute("SELECT * FROM register_loads ORDER BY source")]
    meta = {"generatedAt": generated, "jobs": len(rows), "sources": sources, "registers": registers}

    for name, obj in (("jobs.json", jobs), ("market.json", market), ("meta.json", meta)):
        (out_dir / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out_dir, len(rows)
