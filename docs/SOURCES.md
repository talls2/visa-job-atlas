# Job sources

What the pipeline polls, what was evaluated and left out, and why. Checked on 29 October 2026. Every source below was tested with a real request and judged by its content (live postings dated October 2026), not by the HTTP status alone.

Rules the pipeline follows:
- It reads only what a site's robots.txt and terms allow.
- It identifies itself with a User-Agent that links to this repo.
- It waits between requests to the same site, and longer where a crawl delay is asked.
- Where a source needs one request per posting, it fetches only new postings and caches the answer.
- It needs no account, key or token.

## Polled

### Employer boards (232 configured; 215 active)

Public applicant-tracking-system boards, the same JSON each company's careers page uses:

| ATS | Boards | Notes |
|---|---|---|
| Workday | 85 | Searched per board. Descriptions are fetched once per new posting, at most 120 a board per run. |
| Greenhouse | 75 | |
| Ashby | 34 | |
| Lever | 11 | |
| Workable, Recruitee, Personio | 3, 3, 1 | |
| Amazon, Google, Microsoft | 1 each | Searched by query. |
| SmartRecruiters | 17, **paused** | `api.smartrecruiters.com/robots.txt` disallows every crawler except LinkedInBot. This pauses Bosch, Continental, Canva, Delivery Hero, Grab, ServiceNow, Experian and others until SmartRecruiters allows it. |

The 102 employers added in October 2026 cover medtech, pharma, finance, consumer goods, industrial, aerospace, logistics, energy and healthcare. For each one:
- its board returned live postings when it was added;
- its name was matched against the sponsor registers (UK, Netherlands, Denmark, Ireland, Canada, US).

Two of them state sponsorship in their own postings: Archer Aviation and Flexport.

### Feeds (20)

| Feed | Countries | Fields | Visa signal |
|---|---|---|---|
| **EURES** (European Labour Authority) | DE NL SE DK FI IE LU EE PT ES NO CH | All. Searched by ISCO occupation code, ads that require English only | Medium. The `euresFlag` marks cross-border recruiting. Re-use is allowed with attribution; 10 s crawl delay. |
| **NHS Jobs** (NHSBSA XML API) | GB | Healthcare, plus NHS engineering, finance and HR | **Strong.** Every advert answers whether Skilled Worker applicants are welcome ("Certificate of Sponsorship"). |
| Bundesagentur für Arbeit | DE | All 18 fields (about 45 searches) | Weak. A general board; Germany has no public sponsor register. |
| JobTech (Arbetsförmedlingen) | SE | All fields | Weak |
| Jobindex | DK | All fields | Weak |
| MyCareersFuture | SG | All fields | Weak; salary shown for the Employment Pass threshold. |
| Arbeitnow | DE, EU | All fields | Medium (visa tags) |
| Berlin Startup Jobs | DE | Engineering, sales, marketing, ops, HR, finance | Weak (English-speaking startups) |
| Relocate.me | EU, global | Tech, engineering, business, nursing | Strong (every listing offers relocation) |
| Landing.jobs | PT, EU | Tech | Medium (relocation field) |
| Japan Dev, TokyoDev | JP | Tech | Strong (sponsorship fields) |
| GermanTechJobs | DE | Tech | Weak |
| HN Who is hiring, r/netsec, Mastodon tags | global | Tech | Medium (VISA tags) |
| Cyber Ireland, CyberSecurityJobsite, ISACA | IE, GB, global | Security | Weak to medium |
| swissdevjobs (browser snapshot) | CH | Tech | Strong (sponsorship field) |

### Sponsor registers

UK licensed sponsors, Ireland employment permits by company, Netherlands IND recognised sponsors, Canada positive LMIAs, Denmark SIRI fast-track and US H-1B employer data. A posting from an employer on the register of the posting's country gets the `register` label.

## Worth adding later

| Source | Why it's worth it | What's needed |
|---|---|---|
| A research/academia track, with AcademicTransfer (NL), Science Careers, Chronicle, Inside Higher Ed, Nature Careers, THE Unijobs and jobRxiv | Universities sponsor routinely: IND recognised sponsors, UK licensed sponsors, cap-exempt US H-1B. All of these have allowed RSS feeds or a sitemap plus JobPosting data. | A `research` track (PhD, postdoc, faculty, lab roles) |
| NAV arbeidsplassen feed (NO) | The best Norwegian source, all fields | A free token requested by email (the maintainer accepts the terms) |
| Adzuna API | The only open-ish multi-country source found for AU, NZ, IE and the US | A free API key |
| Hunt UK Visa Sponsors API | Every listing is from a Home Office licensed sponsor | An API key; the site forbids scraping |
| Common Crawl index, SimplifyJobs listings, the tech-jobs-with-relocation list | Discover more Greenhouse, Lever and Ashby boards to add | Discovery only; link out, don't republish |
| Workday sitemaps (`/{site}/siteMap.xml`) | A lighter way to list a Workday board | An adapter change |

## Evaluated and left out

| Source | Reason |
|---|---|
| SmartRecruiters API | robots.txt disallows all crawlers except LinkedInBot (boards paused, see above) |
| Job Bank Canada | Its terms forbid robots and scrapers. It has LMIA labels, but the open-data CSV has no employer or link. |
| jobs.ac.uk | Its terms forbid reproducing content without permission (ask first) |
| visasponsor.jobs, Jobs in Japan, Daijob | Their terms forbid automated access or republishing |
| EURAXESS, GulfTalent, IamExpat | robots.txt blocks crawlers |
| Bayt, GaijinPot, Jobs Ireland | Return 403 to automated requests |
| UK Find a Job (DWP), Workforce Australia | Unreachable from automated clients |
| SEPE (ES) | robots.txt blocks AI agents |
| USAJOBS | robots.txt `Disallow: /`; federal jobs need citizenship anyway |
| Remotive | robots.txt blocks `/api/` |
| Työmarkkinatori (FI), Job-Room (CH), Jooble, Careerjet, Work24 (KR), Hello Work (JP) | Need a key or a partner agreement |
| Engineering, marketing, finance and HR society job boards (IMechE, IET, ICE, CIM, CIPD, ACCA…) | Most return 403 to automated requests or publish no feed |
| Nature Careers and THE Unijobs RSS | robots.txt blocks the RSS paths (their sitemaps are allowed, see "worth adding later") |

Attribution: job data from EURES is © European Labour Authority, re-used under the EURES legal notice. NHS Jobs data comes from the NHS Business Services Authority job adverts API.
