"""SQLite storage: sponsor registers, job history and market snapshots."""

import datetime as dt
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "atlas.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sponsors (
    country TEXT NOT NULL,
    source  TEXT NOT NULL,
    name    TEXT NOT NULL,
    norm    TEXT NOT NULL,
    weight  REAL NOT NULL,
    detail  TEXT
);
CREATE INDEX IF NOT EXISTS sponsors_norm ON sponsors(country, norm);

CREATE TABLE IF NOT EXISTS register_loads (
    source    TEXT PRIMARY KEY,
    loaded_at TEXT NOT NULL,
    rows      INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    uid         TEXT PRIMARY KEY,          -- ats:slug:ext_id
    company     TEXT NOT NULL,
    ats         TEXT NOT NULL,
    title       TEXT NOT NULL,
    location    TEXT,
    countries   TEXT,                      -- comma-separated ISO-2
    url         TEXT,
    posted_at   TEXT,
    department  TEXT,
    salary      TEXT,
    remote      INTEGER,
    family      TEXT,                      -- security | software | data | devops | embedded | qa | product | design
    seniority   TEXT,
    source      TEXT,                      -- employer board or "[feed] name"
    skills      TEXT,                      -- comma-separated skill ids (knowledge/skills.json)
    langs       TEXT,                      -- comma-separated non-English languages required
    visa_pos    TEXT,                      -- posting mentions visa/immigration support
    visa_reloc  TEXT,                      -- posting mentions relocation help (weaker)
    visa_neg    TEXT,                      -- posting rules sponsorship out
    evidence    TEXT,                      -- sponsor-register matches
    register_in TEXT,                      -- comma-separated countries whose register lists the employer
    label       TEXT,                      -- scoring.visa_label
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL,
    closed_at   TEXT
);
CREATE INDEX IF NOT EXISTS jobs_open ON jobs(closed_at, family);

-- One row per company per run: the raw material for market-movement charts.
CREATE TABLE IF NOT EXISTS snapshots (
    run_at     TEXT NOT NULL,
    company    TEXT NOT NULL,
    total_open INTEGER NOT NULL,
    kept       INTEGER NOT NULL,
    ok         INTEGER NOT NULL,
    error      TEXT,
    PRIMARY KEY (run_at, company)
);
"""


# Columns added after the first release; connect() adds any that are missing.
MIGRATIONS = {}


def connect(path=DB_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=60)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    for table, cols in MIGRATIONS.items():
        have = {r["name"] for r in con.execute(f"PRAGMA table_info({table})")}
        for col, typ in cols.items():
            if col not in have:
                con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
    con.commit()
    return con


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat(sep=" ")
