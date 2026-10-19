"""Command line: python -m jobtracker <command>."""

import argparse
import datetime as dt
import json
import os
import sys

from . import ats, db, export, pipeline, registers


def _split(s):
    return {x.strip().lower() for x in s.split(",")} if s else None


def cmd_registers(args, con):
    print("Refreshing sponsor registers...")
    pipeline.update_registers(con, only=_split(args.only), force=args.force)


def cmd_poll(args, con):
    cfg = pipeline.load_config()
    if not con.execute("SELECT 1 FROM sponsors LIMIT 1").fetchone():
        print("No sponsor registers loaded yet - run `registers` first for register evidence.")
    print(f"Polling {len(cfg['companies'])} employer job boards and {len(cfg['feeds'])} feeds...")
    run_at, t = pipeline.poll(con, cfg, only=_split(args.only), workers=args.workers)
    print(f"Done {run_at}: {t['sources']} sources ({t['failed']} failed), {t['relevant']} relevant postings, {t['new']} new.")


def cmd_export(args, con):
    path, n = export.build(con)
    print(f"Wrote jobs.json, market.json and meta.json to {path} ({n} postings)")


def cmd_run(args, con):
    """Refresh stale registers, poll every board, export the site data."""
    stale = True
    row = con.execute("SELECT MIN(loaded_at) FROM register_loads").fetchone()[0]
    loaded = con.execute("SELECT COUNT(*) FROM register_loads").fetchone()[0]
    if row and loaded >= len(registers.LOADERS):
        stale = (dt.datetime.now() - dt.datetime.fromisoformat(row)).days >= 6
    if stale or args.force:
        args.only = None
        cmd_registers(args, con)
    args.only = None
    cmd_poll(args, con)
    cmd_export(args, con)


def cmd_sponsor(args, con):
    q = " ".join(args.name)
    hits = pipeline.sponsor_matches(con, [q], args.country.upper() if args.country else None)
    if not hits:
        print(f"No register entries match '{q}'. Try a shorter or legal name (e.g. 'Stripe Technology').")
    for r in hits[:40]:
        print(f"  {r['country']}  {r['name']:<55} {r['detail']}")


def cmd_discover(args, con):
    cfg = pipeline.load_config()
    known = {c["name"].lower() for c in cfg["companies"]}
    added = []
    for name in args.names:
        hits = ats.discover(name)
        if not hits:
            print(f"  {name}: no public Greenhouse/Lever/Ashby/SmartRecruiters/Workable/Recruitee/Personio board found")
            continue
        for a, slug, n in hits:
            print(f"  {name}: {a}:{slug} ({n} jobs)")
        if args.add and name.lower() not in known:
            a, slug, _ = max(hits, key=lambda h: h[2])
            cfg["companies"].append({"name": name, "ats": a, "slug": slug, "aliases": [], "sponsorship": None, "notes": "added by discover"})
            added.append(name)
    if added:
        with open(pipeline.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Added to companies.json: {', '.join(added)}")


def cmd_trend(args, con):
    rows = con.execute("""
        SELECT run_at, COUNT(*) boards, SUM(total_open) total, SUM(kept) kept
        FROM snapshots WHERE ok = 1 GROUP BY run_at ORDER BY run_at""").fetchall()
    print(f"{'poll':<20}{'sources':>8}{'listed':>8}{'tech':>8}")
    for r in rows:
        print(f"{r['run_at']:<20}{r['boards']:>8}{r['total']:>8}{r['kept']:>8}")
    print("Note: totals change when you add or remove employers.")


def cmd_fresh(args, con):
    """Print "yes" when the last poll is recent and covered most sources, else "no"."""
    cfg = pipeline.load_config()
    expected = sum(1 for c in cfg["companies"] if c.get("enabled", True)) + sum(1 for f in cfg["feeds"] if f.get("enabled", True))
    row = con.execute("SELECT run_at, COUNT(*) n FROM snapshots GROUP BY run_at ORDER BY run_at DESC LIMIT 1").fetchone()
    if not row:
        print("no")
        return
    age_h = (dt.datetime.fromisoformat(db.now()) - dt.datetime.fromisoformat(row["run_at"])).total_seconds() / 3600
    print("yes" if age_h < args.max_age and row["n"] >= 0.9 * expected else "no")


def cmd_test(args, con):
    import unittest
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    suite = unittest.defaultTestLoader.discover(str(root / "tests"), top_level_dir=str(root))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)


def main(argv=None):
    if os.name == "nt":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="jobtracker", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("registers", help="download/refresh government sponsor registers")
    s.add_argument("--only", help="comma list of: uk,ie,ca,nl,dk,us")
    s.add_argument("--force", action="store_true", help="ignore the 6-day download cache")
    s.set_defaults(fn=cmd_registers)

    s = sub.add_parser("poll", help="poll employer job boards and feeds")
    s.add_argument("--only", help="comma list of company names or slugs")
    s.add_argument("--workers", type=int, default=8)
    s.set_defaults(fn=cmd_poll)

    s = sub.add_parser("export", help="write the web app's data files to site/public/data")
    s.set_defaults(fn=cmd_export)

    s = sub.add_parser("run", help="registers (if stale) + poll + export")
    s.add_argument("--force", action="store_true")
    s.add_argument("--workers", type=int, default=8)
    s.set_defaults(fn=cmd_run)

    s = sub.add_parser("sponsor", help="look up an employer in the sponsor registers")
    s.add_argument("name", nargs="+")
    s.add_argument("--country", help="ISO-2 filter, e.g. IE")
    s.set_defaults(fn=cmd_sponsor)

    s = sub.add_parser("discover", help="find a company's public ATS board")
    s.add_argument("names", nargs="+", help='company names, e.g. "Trade Republic" Wise')
    s.add_argument("--add", action="store_true", help="append found boards to config/companies.json")
    s.set_defaults(fn=cmd_discover)

    s = sub.add_parser("trend", help="print totals per poll")
    s.set_defaults(fn=cmd_trend)

    s = sub.add_parser("fresh", help='print "yes" if the last poll is recent and complete')
    s.add_argument("--max-age", type=float, default=20, help="hours")
    s.set_defaults(fn=cmd_fresh)

    s = sub.add_parser("test", help="run the regression tests")
    s.set_defaults(fn=cmd_test)

    args = p.parse_args(argv)
    con = db.connect()
    try:
        args.fn(args, con)
    finally:
        con.close()


if __name__ == "__main__":
    main()
