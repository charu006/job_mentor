import argparse
import logging

from job_mentor import runner

run_collection = runner.run_collection


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Job Mentor collection pipeline.")
    parser.add_argument("--db", dest="db_path", default=None, help="Path to the SQLite database file.")
    parser.add_argument("--days", dest="days", type=int, default=None, help="Override the 14-day collection window.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_collection(db_path=args.db_path, days=args.days)

    print("Job Mentor collection run")
    print("========================")
    print(f"Started: {summary.run_started_at.isoformat()}")
    print(f"Timezone: {summary.timezone_name}")
    print()
    print("Collectors:")
    for collector in runner.discover_collectors():
        name = getattr(collector, "source_name", collector.__class__.__name__)
        if not getattr(collector, "enabled", False):
            print(f"  {name:<24} SKIPPED (disabled)")
        elif name in summary.successful_collectors:
            print(f"  {name:<24} OK")
        elif name in summary.failed_collectors:
            print(f"  {name:<24} FAILED")
        else:
            print(f"  {name:<24} OK")

    print()
    print("Results:")
    print(f"  Raw jobs: {summary.raw_jobs_collected}")
    print(f"  Within {runner.settings.search_window_days if hasattr(runner.settings, 'search_window_days') else 14} days: {summary.jobs_in_window}")
    print(f"  Relevant: {summary.relevant_jobs}")
    print(f"  New: {summary.new_jobs}")
    print(f"  Duplicates: {summary.duplicates}")
    print(f"  Failed collectors: {len(summary.failed_collectors)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
