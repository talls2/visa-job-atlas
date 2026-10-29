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
MAX_NEW_DETAILS = 120  # per board and run


def _fetch_company(company, known=frozenset()):
    """`known` holds the uids already in the database: boards that need one
    request per posting for its description (Workday, SmartRecruiters) only
    make it for new postings."""
    fetch = ats.FETCHERS[company["ats"]]
    prefix = f"{company['ats']}:{company['slug']}:"
    # Big boards are searched, not listed. "query" may hold several searches
    # separated by ";" (e.g. "engineer;marketing;finance"); results are merged.
    queries = [q.strip() for q in (company.get("query") or "").split(";") if q.strip()]
    if company["ats"] in ("google", "microsoft"):
        calls = [((q,), {}) for q in queries or ["software engineer"]]
    elif company["ats"] == "amazon":
        calls = [((q,), {}) for q in [company["slug"]] + queries]
    elif queries and company["ats"] in ("workday", "smartrecruiters"):
        calls = [((company["slug"],), {"query": q}) for q in queries]
    else:
        calls = [((company["slug"],), {})]
    jobs, seen = [], set()
    for args, kwargs in calls:
        for j in fetch(*args, **kwargs):
            key = j.get("url") or j.get("ext_id")
            if key not in seen:
                seen.add(key)
                jobs.append(j)
    relevant, details = [], 0
    for j in jobs:
        family = families.job_family(j["title"])
        if family:
            j["family"] = family
            if j.get("description") is None and prefix + j["ext_id"] in known:
                j["_known"] = True  # keep the details stored on the first sighting
                relevant.append(j)
            elif j.get("description") is None and j.get("_detail"):
                # New postings that need their own request: a few a run, the rest
                # wait for the next run, so a big new board fills in over days.
                if details < MAX_NEW_DETAILS:
                    details += 1
                    relevant.append(ats.fetch_description(j))
            else:
                relevant.append(j)
    return jobs, relevant


def _fetch_feed(feed):
    jobs = feeds.FEEDS[feed["type"]](**feed.get("params", {}))
    relevant = []
    for j in jobs:
        # Community posts (HN, Mastodon) put the role in the body, not a title field.
        # The title decides; a feed's official occupation code (EURES) is the fallback.
        family = families.job_family(j["title"]) or j.get("family") or (families.job_family(j["description"][:200]) if not j.get("company") else None)
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
    # Postings from a paused board are no longer checked, so stop showing them.
    with con:
        for c in cfg["companies"]:
            if not c.get("enabled", True):
                prefix = f"{c['ats']}:{c['slug']}:"
                con.execute("UPDATE jobs SET closed_at = ? WHERE substr(uid, 1, ?) = ? AND closed_at IS NULL",
                            (run_at, len(prefix), prefix))
    known = frozenset(r["uid"] for r in con.execute("SELECT uid FROM jobs"))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch_company, src, known) if kind == "company" else pool.submit(_fetch_feed, src): (kind, src)
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
                    if j.get("_known"):
                        con.execute("UPDATE jobs SET title = ?, family = ?, last_seen = ?, closed_at = NULL WHERE uid = ?",
                                    (j["title"], j["family"], run_at, uid))
                        continue
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
