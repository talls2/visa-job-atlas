"""Register refresh and ATS polling."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from . import ats, db, families, feeds, names, registers, scoring

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "companies.json"


def load_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("target_countries", [])
    cfg.setdefault("companies", [])
    cfg.setdefault("feeds", [])
    return cfg


# ------------------------------------------------------------------ registers
def update_registers(con, only=None, force=False, log=print):
    for key, loader in registers.LOADERS.items():
        if only and key not in only:
            continue
        try:
            rows = loader(force=force)
        except Exception as e:  # keep the other registers going
            log(f"  {key}: FAILED - {e}")
            continue
        if not rows:
            log(f"  {key}: no rows parsed - keeping previous data")
            continue
        source = rows[0]["source"]
        with con:
            con.execute("DELETE FROM sponsors WHERE source = ?", (source,))
            con.executemany(
                "INSERT INTO sponsors (country, source, name, norm, weight, detail) VALUES (?,?,?,?,?,?)",
                [(r["country"], r["source"], r["name"], names.normalize(r["name"]), r["weight"], r["detail"]) for r in rows],
            )
            con.execute("INSERT OR REPLACE INTO register_loads VALUES (?,?,?)", (source, db.now(), len(rows)))
        log(f"  {key}: {len(rows):,} sponsors ({source})")


def sponsor_matches(con, aliases, country=None):
    """Register rows whose entity name matches any alias (optionally in one country)."""
    hits = {}
    for alias in aliases:
        a = names.normalize(alias)
        if not a:
            continue
        q = "SELECT * FROM sponsors WHERE (norm = ? OR norm LIKE ?)"
        args = [a, a + " %"]
        if country:
            q += " AND country = ?"
            args.append(country)
        for r in con.execute(q, args):
            if names.matches(a, r["norm"]):
                hits[(r["source"], r["name"])] = r
    return sorted(hits.values(), key=lambda r: -r["weight"])


# ---------------------------------------------------------------------- poll
def _fetch_company(company):
    if company["ats"] in ("google", "microsoft"):
        # These boards are searched, not listed: the first argument is the search text.
        jobs = ats.FETCHERS[company["ats"]](company.get("query") or "software engineer")
    else:
        kwargs = {"query": company["query"]} if company.get("query") and company["ats"] in ("workday", "smartrecruiters") else {}
        jobs = ats.FETCHERS[company["ats"]](company["slug"], **kwargs)
    relevant = []
    for j in jobs:
        family = families.job_family(j["title"])
        if family:
            j["family"] = family
            relevant.append(ats.fetch_description(j))
    return jobs, relevant


def _fetch_feed(feed):
    jobs = feeds.FEEDS[feed["type"]](**feed.get("params", {}))
    relevant = []
    for j in jobs:
        # Community posts (HN, Mastodon) put the role in the body, not a title field.
        family = families.job_family(j["title"]) or (families.job_family(j["description"][:200]) if not j.get("company") else None)
        if family:
            j["family"] = family
            relevant.append(j)
    return jobs, relevant


def poll(con, cfg, only=None, workers=8, log=print):
    match = lambda *keys: not only or any((k or "").lower() in only for k in keys)
    sources = [("company", c) for c in cfg["companies"] if c.get("enabled", True) and match(c["name"], c["slug"])]
    sources += [("feed", f) for f in cfg.get("feeds", []) if f.get("enabled", True) and match(f["name"], f["type"])]
    run_at = db.now()
    evidence_cache = {}

    def evidence_for(name, aliases, country):
        key = (name.lower(), country)
        if key not in evidence_cache:
            evidence_cache[key] = [(country, r["weight"], r["detail"] + f" [{r['name']}]")
                                   for r in sponsor_matches(con, [name] + aliases, country)[:3]] if name else []
        return evidence_cache[key]

    totals = {"sources": 0, "failed": 0, "relevant": 0, "new": 0}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch_company if kind == "company" else _fetch_feed, src): (kind, src)
                   for kind, src in sources}
        for fut in as_completed(futures):
            kind, src = futures[fut]
            label_name = src["name"] if kind == "company" else f"[feed] {src['name']}"
            prefix = f"{src['ats']}:{src['slug']}:" if kind == "company" else f"feed:{src['type']}:"
            totals["sources"] += 1
            try:
                jobs, relevant = fut.result()
            except Exception as e:
                totals["failed"] += 1
                log(f"  ! {label_name}: {e}")
                with con:
                    con.execute("INSERT OR REPLACE INTO snapshots VALUES (?,?,?,?,?,?)",
                                (run_at, label_name, 0, 0, 0, str(e)[:300]))
                continue

            seen, new_here = set(), 0
            with con:
                for j in relevant:
                    uid = prefix + j["ext_id"]
                    if uid in seen:
                        continue
                    seen.add(uid)
                    company = src["name"] if kind == "company" else (j.get("company") or "")
                    aliases = src.get("aliases", []) if kind == "company" else []
                    policy = src.get("sponsorship") if kind == "company" else None
                    ctry = scoring.countries(j["location"]) or ({j["default_country"]} if j.get("default_country") else set())
                    remote = bool(j.get("remote")) or bool(scoring.REMOTE_RX.search(j["location"] or ""))
                    desc = j.get("description") or ""
                    pos, reloc, neg = scoring.visa_signals(desc)
                    ev = [e for ct in sorted(ctry) for e in evidence_for(company, aliases, ct)]
                    label = scoring.visa_label(pos, reloc, neg, ev, policy)
                    row = dict(
                        uid=uid, company=company or "(unknown)", ats=src["ats"] if kind == "company" else src["type"],
                        source=label_name, title=j["title"], location=j["location"],
                        countries=",".join(sorted(ctry)), url=j["url"], posted_at=j["posted_at"],
                        department=j.get("department"), salary=j.get("salary"), remote=int(remote), family=j["family"],
                        seniority=scoring.seniority(j["title"]), skills=",".join(families.skills(j["title"] + "\n" + desc)),
                        langs=",".join(families.required_languages(desc)), visa_pos=" || ".join(pos),
                        visa_reloc=" || ".join(reloc), visa_neg=" || ".join(neg),
                        evidence=" || ".join(f"{ct}: {d}" for ct, _, d in ev),
                        register_in=",".join(sorted({ct for ct, _, _ in ev})), label=label,
                    )
                    existing = con.execute("SELECT uid FROM jobs WHERE uid = ?", (uid,)).fetchone()
                    if existing:
                        sets = ", ".join(f"{k} = :{k}" for k in row if k != "uid")
                        con.execute(f"UPDATE jobs SET {sets}, last_seen = :now, closed_at = NULL WHERE uid = :uid",
                                    {**row, "now": run_at})
                    else:
                        new_here += 1
                        cols = ", ".join(row) + ", first_seen, last_seen"
                        vals = ", ".join(f":{k}" for k in row) + ", :now, :now"
                        con.execute(f"INSERT INTO jobs ({cols}) VALUES ({vals})", {**row, "now": run_at})
                # Anything from this source we did not see this time has closed.
                open_before = con.execute("SELECT uid FROM jobs WHERE substr(uid, 1, ?) = ? AND closed_at IS NULL",
                                          (len(prefix), prefix))
                gone = [r["uid"] for r in open_before if r["uid"] not in seen]
                con.executemany("UPDATE jobs SET closed_at = ? WHERE uid = ?", [(run_at, u) for u in gone])
                con.execute("INSERT OR REPLACE INTO snapshots VALUES (?,?,?,?,?,?)", (
                    run_at, label_name, len(jobs), len(seen), 1, None))
            totals["relevant"] += len(seen)
            totals["new"] += new_here
            log(f"  {label_name:<30} {len(jobs):>4} listed, {len(seen):>3} relevant, {new_here:>3} new, {len(gone):>3} closed")
    return run_at, totals
