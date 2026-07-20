#!/usr/bin/env python3
"""
Log File Analyzer
-----------------
A CLI tool that reads one or more .log files from a "logs/" folder,
counts INFO, WARNING, ERROR, and CRITICAL messages, displays a
formatted summary in the terminal, shows common error messages,
and saves reports as both report.json and report.csv.

Usage:
    python3 analyzer.py
    python3 analyzer.py --logs-dir /path/to/logs
    python3 analyzer.py --start-date 2025-01-15 --end-date 2025-01-16
    python3 analyzer.py --top-errors 10
    python3 analyzer.py --no-json
"""

import argparse
import sys
import time
from pathlib import Path

from log_reader import LogReader
from log_analyzer import LogAnalyzer
from report import Report


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace with parsed flags.
    """
    parser = argparse.ArgumentParser(
        description="Analyze .log files from a directory — count INFO, WARNING, ERROR, CRITICAL levels.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                          Analyze logs/ folder (default)
  %(prog)s --logs-dir /var/logs                     Analyze a custom logs directory
  %(prog)s --start-date 2025-01-15 --end-date 2025-01-16    Filter by date range
  %(prog)s --top-errors 10                          Show top 10 error messages
  %(prog)s --no-json                                Skip JSON export
  %(prog)s --start-date 2025-01-15 --top-errors 5   Combined filters
        """,
    )

    parser.add_argument(
        "--logs-dir",
        type=str,
        default="logs",
        metavar="PATH",
        help="Path to the directory containing .log files (default: logs/)",
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Inclusive start date for filtering log entries (e.g., 2025-01-15)",
    )

    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        metavar="YYYY-MM-DD",
        help="Inclusive end date for filtering log entries (e.g., 2025-01-16)",
    )

    parser.add_argument(
        "--top-errors",
        type=int,
        default=0,
        metavar="N",
        help="Show top N most frequent ERROR/CRITICAL messages (default: 0 = don't show)",
    )

    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Skip saving report.json (terminal display only)",
    )

    return parser.parse_args()


def main() -> None:
    """
    Main entry point.

    Workflow:
      1. Parse CLI arguments.
      2. Start execution timer.
      3. Discover and read all .log files via LogReader (with optional date filter).
      4. Analyze log levels and extract error messages via LogAnalyzer.
      5. Display formatted report via Report.display().
      6. Display common errors (if --top-errors specified).
      7. Save report.json (unless --no-json).
      8. Save report.csv.
    """
    args = parse_arguments()

    # Start execution timer
    start_time = time.perf_counter()

    # ------------------------------------------------------------------
    # Step 1: Discover and read log files (with optional date filtering)
    # ------------------------------------------------------------------
    reader = LogReader(logs_dir=args.logs_dir)

    try:
        file_contents = reader.read_all(
            start_date=args.start_date,
            end_date=args.end_date,
        )
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2: Analyze log levels
    # ------------------------------------------------------------------
    analyzer = LogAnalyzer()
    analysis_results = analyzer.analyze_all(file_contents)

    # Get common error messages (all of them, Report will limit display)
    common_errors = analyzer.get_common_errors(top_n=args.top_errors if args.top_errors > 0 else 100)

    # Stop execution timer
    elapsed_time = time.perf_counter() - start_time

    # ------------------------------------------------------------------
    # Step 3: Display formatted report
    # ------------------------------------------------------------------
    report = Report(
        analysis_results=analysis_results,
        common_errors=common_errors if args.top_errors > 0 else None,
        execution_time=elapsed_time,
    )

    # Attach date filter info for display
    if args.start_date or args.end_date:
        date_parts = []
        if args.start_date:
            date_parts.append(f"from {args.start_date}")
        if args.end_date:
            date_parts.append(f"to {args.end_date}")
        report.date_filter = " ".join(date_parts)

    report.display()

    # Display common errors if requested
    if args.top_errors > 0 and common_errors:
        report.display_common_errors(top_n=args.top_errors)

    # ------------------------------------------------------------------
    # Step 4: Save reports (JSON and CSV)
    # ------------------------------------------------------------------
    if not args.no_json:
        try:
            report.to_json("report.json")
        except IOError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

    # Always save CSV
    try:
        report.to_csv("report.csv")
    except IOError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
