# Data contract

Everything the web app reads lives in `site/public/data/` (generated daily by the pipeline) and `knowledge/` (curated by hand, bilingual). The browser never uploads the CV anywhere; all matching runs client-side.

Bilingual text is always an object `{"en": "...", "pt": "..."}` ("L10n" below). Portuguese is Brazilian Portuguese.

## knowledge/countries.json (curated)

```jsonc
{
  "asOf": "2026-10",
  "countries": [
    {
      "code": "DE",                         // ISO 3166-1 alpha-2
      "name": {"en": "Germany", "pt": "Alemanha"},
      "bloc": "eu",                         // "eu" (EU/EEA free movement), "ch" (Switzerland, EU-linked), or null
      "openness": 3,                        // 1 (hard) .. 5 (very open) for a sponsored non-EU tech hire
      "opennessNote": L10n,                 // one sentence: why this rating
      "routes": [
        {
          "id": "blue-card",
          "name": L10n,                     // "EU Blue Card"
          "summary": L10n,                  // 1-2 sentences: who it fits, how it works
          "salaryMin": {"amount": 45934, "currency": "EUR", "period": "year", "note": L10n} | null,
          "degree": "required" | "or-experience" | "not-required",
          "employerSponsored": true,        // needs a job offer / employer filing
          "processing": L10n | null,        // typical time, if known
          "source": "https://..."
        }
      ],
      "residencePath": L10n,                // how/when permanent residence becomes possible
      "language": {
        "code": "de", "name": L10n,
        "importance": "low" | "medium" | "high",   // how much tech hiring depends on it
        "note": L10n,                              // where it matters (e.g. OEMs, government, daily life)
        "learning": {"target": "B1", "exam": "Goethe-Zertifikat / telc / ÖSD", "hours": L10n} | null
      } | null,                              // null when English is the local language
      "englishWorkplace": "high" | "medium" | "low",
      "catches": [L10n],                    // main obstacles (2-4)
      "recentChanges": [L10n],              // dated rule changes in 2025-2026 (0-4)
      "sponsorRegister": {"name": L10n, "url": "https://..."} | null,
      "jobBoards": [{"name": "Arbeitnow", "url": "https://..."}],
      "cvTips": L10n,                       // local CV conventions
      "sources": ["https://..."]
    }
  ]
}
```

## knowledge/tracks.json (curated)

One track per job family. Family ids (shared with the pipeline, classified in `pipeline/jobtracker/families.py`; `site/src/cv/family.ts` is generated from it by `pipeline/gen_family_ts.py`):

- tech: `security`, `software`, `data`, `devops`, `embedded`, `qa`, `product`
- creative: `design` (UX/UI, product, graphic and brand design), `video` (video editing, motion, colour, post-production)
- engineering: `mechanical` (incl. manufacturing, process, aerospace), `electrical` (power, controls, automation), `civil` (structural, construction, BIM)
- business: `marketing`, `sales` (incl. customer success, solutions engineering), `finance` (accounting, FP&A, tax, risk), `operations` (supply chain, procurement, project management), `people` (HR, recruiting)
- health: `healthcare` (nursing, medicine, pharmacy, allied health)

```jsonc
{
  "asOf": "2026-10",
  "tracks": [
    {
      "id": "security",
      "name": L10n,
      "summary": L10n,
      "niches": [{"id": "appsec", "name": L10n, "summary": L10n, "keywords": ["appsec", "sast"]}],
      "coreSkills": ["python", "linux", "networking"],   // ids from knowledge/skills.json
      "certs": [{"name": "PNPT", "provider": "TCM Security", "level": "entry" | "mid" | "senior",
                 "cost": "~US$399-499", "why": L10n, "url": "https://..."}],
      "projects": [{"title": L10n, "description": L10n, "level": "entry" | "mid"}],
      "firstSponsoredRoles": L10n,          // which roles realistically get a first visa
      "switchTips": {"software": L10n, "...": L10n},     // advice when moving INTO this track from another family
      "weeklyQuests": [L10n],               // small repeatable habits
      "milestones": {"m3": [L10n], "m6": [L10n], "m12": [L10n]},
      "countryNotes": {"GB": L10n}       // optional: licensing/recognition and the usual route for this field per country
    }
  ]
}
```

## knowledge/skills.json (curated)

```jsonc
{"skills": [{"id": "python", "label": "Python", "patterns": ["python"], "families": ["software", "data", "security"]}]}
```
`patterns` are case-insensitive regular-expression fragments matched on word boundaries, in both CV text and job descriptions.

## site/public/data/jobs.json (generated)

Column-oriented to stay small:

```jsonc
{
  "generatedAt": "2026-10-19T09:00:00Z",
  "fields": ["id", "title", "company", "location", "countries", "url", "posted", "firstSeen",
             "family", "seniority", "remote", "visa", "registerIn", "skills", "langs", "salary"],
  "rows": [["gh:stripe:123", "Backend Engineer", "Stripe", "Dublin", ["IE"], "https://...", "2026-10-01",
            "2026-10-02", "software", "senior", 0, "register", ["IE"], ["java", "aws"], [], ""]]
}
```

- `visa`: `explicit` | `conditional` | `relocation` | `register` | `employer-yes` | `unknown` | `blocked` | `employer-no`
- `registerIn`: countries whose government sponsor register lists this employer
- `langs`: non-English languages the description requires (`de`, `ja`, `fr`, `nl`, `sv`, ...)

## site/public/data/market.json (generated)

```jsonc
{"generatedAt": "...", "cells": {"DE|software": {"jobs": 410, "visaFriendly": 37, "englishOk": 260, "skills": {"java": 120, "aws": 88}}}}
```

`englishOk` counts postings that require no language other than English.

## site/public/data/meta.json (generated)

```jsonc
{"generatedAt": "...", "sources": [{"name": "Stripe", "kind": "board", "ok": true, "listed": 520, "kept": 140}],
 "registers": [{"source": "UK sponsor register", "country": "GB", "rows": 120000, "loadedAt": "2026-10-15"}]}
```
