# Job Mentor

Job Mentor is a Python-based monitoring system for discovering European jobs in materials, polymer, elastomer, and related R&D roles.

## Purpose

The system is designed to monitor job portals and detect roles substantially related to:

- elastomers
- polymers
- rubber technology
- materials development
- product/material development
- polymer science
- formulation, compounding and related technical R&D work

The project is built in stages, and Stage 4 introduces a deterministic matching engine for elastomer/polymer/material-development relevance.

## Stage 5A portal status

| Portal | Country | Status | Integration method | Credentials required |
| --- | --- | --- | --- | --- |
| Arbeitsagentur | Germany | IMPLEMENTED | Public website fetch via documented interface pattern | No |
| StepStone | Germany | DISABLED / REQUIRES AUTHORIZATION | Not currently automated; safe disabled stub | Yes, if a permitted API contract is later provided |
| meinestadt | Germany | DISABLED / NOT CURRENTLY AUTOMATABLE | Not currently automated; safe disabled stub | No verified public API or feed available |

## Stage 5B Netherlands portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| werk.nl | DISABLED | Safe disabled stub | Automated access is not permitted under the current public terms; no scraper is used |
| Nationale Vacaturebank | DISABLED | Safe disabled stub | No verified public API/feed identified for safe automated access |
| JobDigger | API-KEY REQUIRED | Official API with documented endpoints | Enabled only when `JOBDIGGER_API_KEY` is configured and `JOBDIGGER_ENABLED=true` |

## Stage 5C Switzerland portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| arbeit.swiss | DISABLED | Safe disabled stub | Employer-facing Job-Room interface is not treated as a public vacancy-search API for this project |
| jobs.ch | DISABLED | Safe disabled stub | JobCloud employer/recruiting platform; automated scraping is not authorized |
| jobup.ch | DISABLED | Safe disabled stub | JobCloud employer/recruiting platform; no verified public retrieval API/feed identified |

## Stage 5D Denmark portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| jobnet.dk | DISABLED | Safe disabled stub | Public candidate-facing job search exists, but the current official employer-side material is controlled and no documented public vacancy-search API/feed is accepted for automated retrieval |
| ofir.dk | DISABLED | Safe disabled stub | The current official site is closed (HTTP 410) and no supported public retrieval interface is available |
| workindenmark.dk | DISABLED | Safe disabled stub | Public information portal directing to Jobnet-hosted vacancy search; no verified public API/feed is accepted for automation |

## Stage 5E Ireland portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| publicjobs.ie | DISABLED | Safe disabled stub | Official terms restrict copying/reproduction for personal, non-commercial use; the project does not treat public visibility as permission to scrape |
| irishjobs.ie | DISABLED | Safe disabled stub | The Stepstone Group Ireland Recruit Limited terms restrict removing website content by competitive means; no documented public partner API or permitted automated retrieval mechanism is used |
| recruitireland.com | DISABLED | Safe disabled stub | Public viewing is allowed within intended use, but no verified public API/feed or explicitly permitted automated interface was identified for this project |
## Stage 5F Portugal portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| emprego.iefp.pt | DISABLED | Safe disabled stub | The current public IEFP experience does not provide a documented public vacancy API/feed or explicitly permitted automated retrieval interface |
| net-empregos.com | ACTIVE via official RSS feed | Official feed | Uses the public RSS feed published by the site itself; no credential or scraping bypass is used |
| beebez.pt | DISABLED / domain not current | Safe disabled stub | The requested beebez.pt domain is not treated as a current public job portal and no verified public jobs API/feed was identified |

## Stage 5G Finland portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| tyomarkkinatori.fi | DISABLED | Safe disabled stub | The official access model requires activation, business-ID validation, KEHA checks and credentials; this project does not have that organisational approval |
| duunitori.fi | DISABLED | Safe disabled stub | No verified public vacancy API/feed or explicitly permitted automated retrieval interface was identified; public access alone is not treated as permission to scrape |
| monster.fi | DISABLED | Safe disabled stub | The current service is effectively a bot-gated/rebranded Jobly-style flow with no verified public retrieval contract; it is not treated as an independently active portal |

## Stage 5H Sweden portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| Arbetsförmedlingen / Platsbanken | ACTIVE via official public API | Public JobSearch API | Uses the official JobSearch API with public access, no API key or registration required, and no HTML scraping. This project uses the documented API rather than the website front end. |
| Academic Work Sweden | DISABLED | Safe disabled stub | No clearly documented public vacancy API/feed intended for automated retrieval was identified; public site visibility does not establish permission to scrape. |
| JobbSafari | DISABLED | Safe disabled stub | Current terms allow ordinary links but prohibit systematic copying/scraping and competing or substantially similar use without explicit written approval. |

Official API/access rationale: Arbetsförmedlingen’s official JobSearch API is a public, documented JSON interface under the official jobtech/open-data model and is used directly. Academic Work Sweden and JobbSafari are kept disabled because no verified public API/feed or approved retrieval model was identified, and the current terms restrict automated or competing use.

## Stage 5I Norway portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| Arbeidsplassen / NAV | ACTIVE via official public API | Public ads API | Uses the official public NAV/Arbeidsplassen job-ad API surface. No HTML scraping is used. |
| FINN.no | DISABLED | Safe disabled stub | FINN’s current public interface is treated as out-of-scope for automated retrieval without documented public permission and a permitted interface. |
| Jobbnorge | ACTIVE via official RSS feed | Official RSS feed | Uses the public Jobbnorge RSS feed only; no browser scraping or bypass is used. |

Official access rationale: NAV/Arbeidsplassen exposes a public job-ad API surface and is treated as the active official API path for this project. Jobbnorge publishes a public RSS feed and is used as the official feed-based collector. FINN remains disabled because the current public website and business-facing publishing model does not provide a clearly documented public retrieval API/feed contract for automated monitoring in this project. The NAV collector uses a conservative global request cap of 10 requests per collector run, configurable via `ARBEIDSPLASSEN_MAX_REQUESTS`.

## Stage 5J Poland portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| pracuj.pl | DISABLED | Safe disabled stub | Public job-search pages exist, but no verified documented public vacancy-search API/feed authorized for this project has been identified. Public website access is not treated as permission to scrape or reverse-engineer non-public interfaces. |
| nofluffjobs.com | DISABLED | Safe disabled stub | The current official terms prohibit downloading or systematically reusing job-board data, including individual advertisements, unless separately authorized. This project does not bypass those restrictions via browser automation, undocumented endpoints, or scraping. |
| rocketjobs.pl | DISABLED | Safe disabled stub | The official terms prohibit copying, downloading, or distributing application content and database material without prior written permission. No documented public API/feed or explicit permission for automated retrieval has been identified. |

Official access rationale: Each of these Polish portals remains disabled by default because the project only permits collection from documented, clearly authorized public interfaces. The project does not treat public form pages or browser-visible content as permission to scrape or bypass terms, and no undocumented private API endpoints or hidden browser-network workarounds are used.

## Stage 5K Luxembourg portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| adem.public.lu | DISABLED | Safe disabled stub | Public vacancies may be visible, but no verified official public vacancy-search API/feed has been documented and authorized for this project. Public visibility is not treated as permission to scrape or reverse-engineer frontend endpoints. |
| jobs.lu | DISABLED | Safe disabled stub | Official terms are intended for individual job searching and prohibit using the service to develop other services. No verified public vacancy API/feed for this project was identified. |
| moovijob.com | DISABLED | Safe disabled stub | Official terms prohibit illicit access and actions that compromise proper operation of the platform. No documented public API/feed authorized for automated collection was identified. |

Official access rationale: The Luxembourg portals remain disabled by default because this project only collects from documented, explicitly permitted public APIs/feeds. Publicly visible pages, candidate-facing job search flows, and browser-discoverable content are not treated as authorization to scrape, automate, or reverse-engineer private interfaces.

## Stage 5L EU-wide / Euraxess portal status

| Portal | Status | Integration | Notes |
| --- | --- | --- | --- |
| EURES / Europass Find Jobs | DISABLED | Safe disabled stub | The public Europass job-search experience is backed by the EURES labour-mobility portal, but no verified public vacancy-search API/feed was identified that is clearly authorized for this project. The project treats the public front end as an interface to EURES data rather than as a separate independent API source and does not create duplicate collectors for the same underlying vacancy database. |
| EURAXESS | DISABLED | Safe disabled stub | The current official domain is https://euraxess.ec.europa.eu/. Legacy domains such as thenetwork.euraxesss.org and euraxess.eu are not treated as the active public retrieval source. No documented public vacancy-search API/feed was identified that authorizes automated retrieval for this project. |
| jobsireland.eu | DISABLED | Safe disabled stub | This is not the same service as jobsireland.ie. This domain is treated separately and remains disabled unless a documented public retrieval contract is verified. |
| Trello | NOT A GENERIC JOB PORTAL | Not implemented | Trello is not treated as a generic job portal. No specific public board/list was identified that is clearly authorized as a legitimate job source for this project, so no Trello collector is created. |

Official access rationale: EURES and EURAXESS are handled conservatively under the project’s safe-disabled policy. The project does not assume that a public website or a public vacancy page is an authorized automated retrieval endpoint. For EURES, Europass is treated as an interface over the EURES vacancy database rather than a separate vendor-specific collector. For EURAXESS, the current official domain is verified as https://euraxess.ec.europa.eu/; legacy domains are documented as obsolete or redirected rather than treated as independent sources. For jobsireland.eu, the project keeps the domain distinct from jobsireland.ie and requires explicit public authorization before any automated collection is allowed. Trello is explicitly documented as not being a generic job portal for this project unless a specific public board and API contract are confirmed.

## Matching engine purpose

The matching engine is intended to score a job based on how strongly it matches the intended job family:

- elastomer and rubber technology
- polymer science and polymer technology
- materials development and materials engineering
- product development in polymer/elastomer/rubber contexts
- research and development roles where technical materials context is present

It is designed to be deterministic, explainable, and testable without requiring an external LLM.

## Core keyword groups

The matching engine uses a centralized taxonomy in [job_mentor/matching/config.py](job_mentor/matching/config.py), grouped into:

- core elastomer/polymer keywords
- related elastomer and rubber terms
- polymer engineering and chemistry terms
- materials development and materials science terms
- product-development keywords
- R&D keywords
- formulation and compounding terms
- German technical terminology
- exclusion/context penalties for irrelevant roles

## Scoring concept

The engine calculates a score from 0 to 100 for each job based on weighted matches in:

- job title
- job description
- company metadata
- location metadata

Title matches receive higher weight than incidental description-only mentions. Repeated technical terms and relevant context increase the score. Generic roles remain constrained by contextual relevance.

## Thresholds

The current configurable thresholds are:

- 80–100: STRONG_MATCH
- 60–79: GOOD_MATCH
- 40–59: POSSIBLE_MATCH
- below 40: IRRELEVANT

These thresholds are configured in the matching configuration layer and can be changed without changing the matching logic.

## Deterministic and local-only behavior

The Stage 5A portal adapters are intentionally conservative:

- Arbeitsagentur remains implemented and tested
- StepStone remains disabled unless a permitted, verified API or authorization flow is provided
- Meinestadt remains disabled unless a documented public mechanism is available
- no unauthorized scraping is attempted
- no credentials or personal sessions are added

## Architecture overview

The project remains structured into modular layers:

- `job_mentor/config`: configuration and environment settings
- `job_mentor/core`: orchestration and pipeline utilities
- `job_mentor/collectors`: portal-specific collectors
- `job_mentor/database`: persistence and deduplication
- `job_mentor/matching`: keyword taxonomy and scoring engine
- `job_mentor/reporting`: daily report generation
- `job_mentor/utils`: shared helpers

## Local setup

1. Create a virtual environment:
   `python -m venv .venv`
2. Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`
3. Install dependencies:
   `pip install -r requirements.txt`
4. Copy the sample environment file:
   `copy .env.example .env` (Windows) or `cp .env.example .env` (Unix-like systems)
5. Run the project entry point:
   `python main.py`

## Notes

- No real credentials or secrets are stored in the repository.
- The matching engine is intentionally local and deterministic.
- Email sending, deployment workflows, and additional portal automation remain intentionally out of scope for this stage.
