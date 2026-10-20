# Visa Job Atlas

**Upload your CV, answer a few questions, and get the countries, open jobs and 12-month plan most likely to get you a visa-sponsored tech job.** English and Brazilian Portuguese.

**Live:** https://talls2.github.io/visa-job-atlas/

Your CV is read inside your browser and never uploaded. The site is static: there is no server and no account.

## What it does

1. **Reads your CV (PDF or text)** with pdf.js and pulls out skills, years of experience, level, degree, certifications and languages. You review and correct it.
2. **Interviews you**, with questions an advisor would ask:
   - citizenships (an EU passport changes everything)
   - where you live and where you'd like to go
   - what matters most to you
   - whether you're staying in your field or switching (security, software, data, DevOps, embedded, QA, product, design, video)
   - willingness to learn a language
   - hours per week, budget and timeline
3. **Ranks 22 countries** with an explanation for every point: visa openness, live demand for your field, language fit, degree rules, free movement for EU citizens.
4. **Matches you to open postings** refreshed every morning. Each one shows its visa signal, your matched skills, skills to learn, and any language you'd need.
5. **Builds a phased plan**, sized to your hours, budget and timeline:
   - skills employers ask for that your CV doesn't show (from live postings)
   - certifications worth it at your level
   - portfolio projects
   - a language plan
   - visa-route steps
   - a weekly routine
6. **Optional: Claude writes it up.** Paste your own Anthropic API key and Claude turns the results into a written, personal plan. The key and CV go only from your browser to Anthropic.

Export the plan as Markdown, or print it to PDF.

## How the data is built

```
government sponsor registers ─┐
employer job boards (130+)  ──┼─► pipeline (Python, stdlib) ─► jobs.json / market.json ─► web app (React, in-browser matching)
job feeds (17)              ──┘        daily on GitHub Actions             published to GitHub Pages
```

- **Sponsor registers:**
  - UK Register of Licensed Sponsors
  - Ireland DETE employment permits by company
  - Netherlands IND recognised sponsors
  - Canada positive LMIAs
  - Denmark SIRI fast-track
  - US USCIS H-1B employer data
- **Employer boards:** public Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Workable, Recruitee and Personio boards, plus Amazon and Google.
- **Feeds:** Japan Dev, TokyoDev, HN "Who is hiring", Arbeitnow, Bundesagentur für Arbeit, GermanTechJobs, JobTech (Sweden), Jobindex (Denmark), Landing.jobs, Relocate.me, MyCareersFuture (Singapore), Mastodon job tags and more.
- **Each posting** gets:
  - a job family and seniority
  - its required skills (from [`knowledge/skills.json`](knowledge/skills.json))
  - any non-English language it requires
  - a visa label: `explicit` (offers sponsorship), `conditional`, `register` (employer is on that country's sponsor register), `relocation`, `unknown`, or `blocked` ("must have the right to work", clearance, citizens only…). Blocked postings are dropped.
- **Countries with no public register** (Germany, Japan, the Nordics…): any employer can file a work permit, so English-language roles there count partially toward demand instead of being treated as "no visa".

Country rules and career tracks are curated by hand in [`knowledge/`](knowledge/), with sources, and rechecked against official pages (rules as of October 2026).

## Run it locally

```bash
# 1. Data (Python 3.10+, no dependencies; first run downloads the registers)
cd pipeline
python -m jobtracker run        # registers + poll + export to site/public/data
python -m jobtracker test

# 2. App (Node 20+)
cd ../site
npm install
npm run dev                     # http://localhost:5173
npm test
```

Pipeline commands: `registers`, `poll`, `export`, `run`, `sponsor <name>` (look an employer up in the registers), `discover <name> --add` (find a company's public job board), `trend`.

## Repository layout

| Path | What |
|---|---|
| `pipeline/` | Job-data pipeline: ATS and feed fetchers, sponsor-register loaders, family/skill/language/visa tagging, SQLite history, JSON export |
| `knowledge/` | Curated, bilingual knowledge: `countries.json` (visa routes, thresholds, residence paths, CV conventions), `tracks.json` (9 career tracks, from software and security to design and video editing), `skills.json` |
| `site/` | The web app: Vite + React + TypeScript; CV parsing (`src/cv`), matching and planning (`src/engine`) |
| `docs/DATA.md` | Data contract between the pipeline and the app |
| `.github/workflows/` | CI (tests + build) and the daily refresh-and-deploy job |

## Adding an employer or a country

- **Employer:** `python -m jobtracker discover "Company Name" --add` finds its public job board and adds it to `pipeline/config/companies.json`.
- **Country:** add an entry to `knowledge/countries.json` following `docs/DATA.md`. Link every number to its official source.

## Disclaimer

This is not legal or immigration advice. Visa rules change often. Confirm every route on the official government page, and with the employer, before you act. Job postings belong to their publishers; the app links to the original posting.

## License

[MIT](LICENSE) © William Benett
