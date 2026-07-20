#!/usr/bin/env python3
"""
Log File Analyzer
-----------------
A CLI tool that reads one or more .log files from a "logs/" folder,
counts INFO, WARNING, ERROR, and CRITICAL messages, displays a
formatted summary in the terminal, and saves the report as report.json.

Usage:
    python3 analyzer.py
    python3 analyzer.py --logs-dir /path/to/logs
    python3 analyzer.py --no-json
"""

import argparse
import sys
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
  %(prog)s                          Analyze logs/ folder (default)
  %(prog)s --logs-dir /var/logs     Analyze a custom logs directory
  %(prog)s --no-json                Display summary only, skip JSON export
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
      2. Discover and read all .log files via LogReader.
      3. Analyze log levels via LogAnalyzer.
      4. Display formatted report via Report.display().
      5. Save report.json via Report.to_json() (unless --no-json).
    """
    args = parse_arguments()

    # ------------------------------------------------------------------
    # Step 1: Discover and read log files
    # ------------------------------------------------------------------
    reader = LogReader(logs_dir=args.logs_dir)

    try:
        file_contents = reader.read_all()
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Step 2: Analyze log levels
    # ------------------------------------------------------------------
    analyzer = LogAnalyzer()
    analysis_results = analyzer.analyze_all(file_contents)

    # ------------------------------------------------------------------
    # Step 3: Display formatted report
    # ------------------------------------------------------------------
    report = Report(analysis_results)
    report.display()

    # ------------------------------------------------------------------
    # Step 4: Save report.json
    # ------------------------------------------------------------------
    if not args.no_json:
        try:
            report.to_json("report.json")
        except IOError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
