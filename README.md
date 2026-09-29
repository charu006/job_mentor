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
