import argparse
import logging

from job_mentor import runner
from job_mentor.config.settings import load_settings
from job_mentor.workflow import run_job_mentor_workflow



def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the Job Mentor workflow pipeline.")
    parser.add_argument("--db", dest="db_path", default=None, help="Path to the SQLite database file.")
    parser.add_argument("--days", dest="days", type=int, default=None, help="Override the 14-day collection window.")
    parser.add_argument("--dry-run", action="store_true", help="Run collection and reporting without sending email.")
    parser.add_argument("--collect-only", action="store_true", help="Run only the collection pipeline and print its summary.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = load_settings()

    if args.collect_only:
        summary = runner.run_collection(db_path=args.db_path, days=args.days)

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
        print(f"  Within {args.days if args.days is not None else settings.search_window_days} days: {summary.jobs_in_window}")
        print(f"  Relevant: {summary.relevant_jobs}")
        print(f"  New: {summary.new_jobs}")
        print(f"  Duplicates: {summary.duplicates}")
        print(f"  Failed collectors: {len(summary.failed_collectors)}")
        return 0

    workflow_result = run_job_mentor_workflow(db_path=args.db_path, days=args.days, dry_run=args.dry_run)
    summary = workflow_result.collection_summary

    print("Job Mentor workflow run")
    print("======================")
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
    print(f"  Within {workflow_result.report.search_window_days} days: {summary.jobs_in_window}")
    print(f"  Relevant: {summary.relevant_jobs}")
    print(f"  New: {summary.new_jobs}")
    print(f"  Duplicates: {summary.duplicates}")
    print(f"  Failed collectors: {len(summary.failed_collectors)}")

    print()
    print("Daily report:")
    print(f"  Date: {workflow_result.report.report_date}")
    print(f"  Timezone: {workflow_result.report.timezone}")
    print(f"  Matching jobs: {workflow_result.report.total_jobs}")

    print()
    if args.dry_run:
        print("Dry run preview:")
        print(f"Recipient: {workflow_result.email.recipient or '<not configured>'}")
        print(f"Subject: {workflow_result.email.subject}")
        print("Body:")
        print(workflow_result.email.plain_text)
    else:
        print("Email sent:")
        print(f"Recipient: {workflow_result.email.recipient or '<not configured>'}")
        print(f"Subject: {workflow_result.email.subject}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
