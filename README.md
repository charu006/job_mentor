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

## Examples

Strong examples:
- Elastomer Development Engineer
- Polymer Scientist
- Rubber Technology Engineer
- Materials Development Engineer – Polymer
- Compound Development Engineer

Good examples:
- Polymer R&D Engineer
- Product Development Engineer – Rubber Components
- Elastomer Specialist

Possible examples:
- Materials Engineer with polymer formulation work
- Mechanical Engineer with polymer seal development responsibilities

Irrelevant examples:
- Software Engineer at a polymer company
- Accountant at a rubber manufacturer
- warehouse or administrative role with no technical material responsibility

## Deterministic and local-only behavior

Stage 4 does not depend on a cloud API or an LLM. The process is:

- deterministic
- local
- explainable
- testable
- configurable

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
- Email sending, additional portals, and GitHub Actions are intentionally not part of this stage.
