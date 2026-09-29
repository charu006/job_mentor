# Job Mentor

Job Mentor is a Python-based monitoring system for discovering European jobs in materials, polymer, elastomer, and related R&D roles.

## Purpose

The system is designed to search multiple European job portals and identify jobs related to:

- elastomers
- polymers
- rubber technology
- materials development
- product/material development
- polymer science
- related research and development positions

The project is intentionally staged so the initial work focuses on a reliable foundation before any scraping or notification logic is added.

## Architecture overview

The project is organized into a small set of modular components:

- `job_mentor/config`: site and keyword configuration, environment-based application settings.
- `job_mentor/core`: logging, orchestration, and runtime setup.
- `job_mentor/collectors`: portal-specific search collectors (planned, not yet implemented).
- `job_mentor/database`: persistence logic for jobs and monitoring history.
- `job_mentor/matching`: keyword filtering and relevance evaluation.
- `job_mentor/notifications`: email and alert delivery logic.
- `job_mentor/utils`: common helpers for dates, URLs, and text normalization.

## Development stages

### Stage 1: Foundation and scaffolding

This is the current stage.

Goals:
- establish a clean project structure
- create configuration for portals and keywords
- provide placeholder modules for future implementation
- add basic tests for imports and configuration loading
- ensure the project can be run in a Python 3.12+ virtual environment

### Stage 2: Data collection

Planned work:
- implement portal-specific collectors
- add job extraction helpers
- support the last 14 days of job postings
- normalize titles, locations, and dates across sources

### Stage 3: Matching and deduplication

Planned work:
- create robust keyword matching
- detect newly discovered jobs only
- prevent duplicate notifications
- persist monitoring history in a database

### Stage 4: Notifications and automation

Planned work:
- email delivery using environment-configured settings
- failure logging without stopping monitoring
- operational improvements for resilience

### Stage 5: Deployment and scheduling

Planned work:
- configure automation for recurring scans
- run in GitHub Actions or a similar scheduler
- document setup and expected runtime behavior

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

- Do not commit real email credentials, API keys, passwords, or secrets.
- Use environment variables for runtime configuration.
- No scraping or production automation is implemented in this stage.
