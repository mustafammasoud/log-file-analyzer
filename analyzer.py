#!/usr/bin/env python3
"""
Log File Analyzer
-----------------
A CLI tool that reads a log file, counts INFO/WARNING/ERROR messages,
displays a formatted summary, exports results to CSV, and searches
for keywords within the log.

Usage:
    python3 analyzer.py                          # Basic analysis
    python3 analyzer.py --export report.csv      # Export to CSV
    python3 analyzer.py --search "error"         # Search for keyword
    python3 analyzer.py --log-file custom.log    # Analyze a custom file
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
#  Helper: Validate and read the log file
# ---------------------------------------------------------------------------

def read_log_file(filepath: str) -> List[str]:
    """
    Reads the log file and returns its lines as a list.
    
    Performs multiple validation checks:
      - File exists
      - File is not a directory
      - File is readable
      - File is not empty
    
    Args:
        filepath: Path to the log file (e.g., "app.log")
    
    Returns:
        List of stripped lines from the file
    
    Raises:
        FileNotFoundError: If the log file doesn't exist
        IsADirectoryError: If the path is a directory
        PermissionError: If the file cannot be read
        ValueError: If the file is empty
    """
    path = Path(filepath)
    
    # --- Validation checks ---
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: '{filepath}'")
    
    if path.is_dir():
        raise IsADirectoryError(f"Expected a file, but '{filepath}' is a directory")
    
    # Check file size before reading (prevents huge file issues)
    file_size = path.stat().st_size
    if file_size == 0:
        raise ValueError(f"Log file is empty: '{filepath}'")
    
    # Attempt to read the file; let Python raise PermissionError naturally
    try:
        with open(path, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
    except PermissionError:
        raise PermissionError(f"Permission denied: cannot read '{filepath}'")
    except OSError as e:
        raise OSError(f"Error reading '{filepath}': {e}")
    
    # Final sanity check on content
    if not lines:
        raise ValueError(f"Log file contains no lines: '{filepath}'")
    
    return lines


# ---------------------------------------------------------------------------
#  Core: Count log levels
# ---------------------------------------------------------------------------

def count_log_levels(lines: List[str]) -> Dict[str, int]:
    """
    Counts occurrences of each log level (INFO, WARNING, ERROR).
    
    Uses regex to find log level patterns in timestamped log entries.
    
    Args:
        lines: List of log file lines
    
    Returns:
        Dictionary mapping log level -> count
    """
    # Initialize counters
    counts = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
    }
    
    # Pattern: YYYY-MM-DD HH:MM:SS LEVEL message
    # Example: "2025-01-15 10:30:45 INFO Application started"
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+(INFO|WARNING|ERROR)\b')
    
    for line in lines:
        if not line:
            continue
        
        match = pattern.search(line)
        if match:
            level = match.group(1)
            counts[level] += 1
    
    return counts


# ---------------------------------------------------------------------------
#  Display: Formatted summary in terminal
# ---------------------------------------------------------------------------

def display_summary(counts: Dict[str, int]) -> None:
    """
    Prints a formatted summary table of log level counts to the terminal.
    
    Args:
        counts: Dictionary with log level counts (from count_log_levels)
    """
    total = sum(counts.values())
    
    print("=" * 40)
    print("         LOG FILE ANALYSIS SUMMARY")
    print("=" * 40)
    print(f"{'LEVEL':<15} {'COUNT':<10}")
    print("-" * 25)
    
    # Display in consistent order
    for level in ["INFO", "WARNING", "ERROR"]:
        count = counts.get(level, 0)
        print(f"{level:<15} {count:<10}")
    
    print("-" * 25)
    print(f"{'TOTAL':<15} {total:<10}")
    print("=" * 40)


# ---------------------------------------------------------------------------
#  Export: Save analysis to CSV
# ---------------------------------------------------------------------------

def export_to_csv(counts: Dict[str, int], output_file: str) -> None:
    """
    Exports the log level counts to a CSV file.
    
    Args:
        counts: Dictionary with log level counts
        output_file: Path for the output CSV file
    
    Raises:
        IOError: If the CSV file cannot be written
    """
    try:
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # Header row
            writer.writerow(["Log Level", "Count"])
            # Data rows (consistent order)
            for level in ["INFO", "WARNING", "ERROR"]:
                writer.writerow([level, counts.get(level, 0)])
            # Summary row
            writer.writerow(["TOTAL", sum(counts.values())])
        
        print(f"[INFO] Report exported to: '{output_file}'")
    
    except IOError as e:
        raise IOError(f"Failed to write CSV file '{output_file}': {e}")


# ---------------------------------------------------------------------------
#  Search: Find keywords in the log
# ---------------------------------------------------------------------------

def search_keyword(lines: List[str], keyword: str) -> List[Dict[str, object]]:
    """
    Searches log lines for a keyword (case-insensitive) and returns
    matching entries with context.
    
    Args:
        lines: List of log file lines
        keyword: The keyword or phrase to search for
    
    Returns:
        List of dictionaries with 'line_number' (1-based) and 'content'
    """
    results = []
    keyword_lower = keyword.lower()
    
    for idx, line in enumerate(lines, start=1):
        if not line:
            continue
        if keyword_lower in line.lower():
            results.append({
                "line_number": idx,
                "content": line
            })
    
    return results


def display_search_results(results: List[Dict[str, object]], keyword: str) -> None:
    """
    Prints search results in a readable format.
    
    Args:
        results: List of matching entries from search_keyword()
        keyword: The keyword that was searched for
    """
    if not results:
        print(f"[INFO] No matches found for keyword: '{keyword}'")
        return
    
    print(f"\n[INFO] Found {len(results)} match(es) for keyword: '{keyword}'\n")
    print("=" * 60)
    print(f"{'LINE':<8} {'CONTENT'}")
    print("=" * 60)
    
    for entry in results:
        line_no = entry["line_number"]
        content = entry["content"]
        # Truncate overly long lines for clean display
        if len(content) > 80:
            content = content[:77] + "..."
        print(f"{line_no:<8} {content}")
    
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
#  CLI Argument Parsing
# ---------------------------------------------------------------------------

def parse_arguments() -> argparse.Namespace:
    """
    Parses command-line arguments.
    
    Returns:
        argparse.Namespace object with parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Analyze a log file and count INFO, WARNING, ERROR messages.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         Analyze app.log (default)
  %(prog)s --log-file server.log   Analyze a custom log file
  %(prog)s --export report.csv     Analyze and export results to CSV
  %(prog)s --search "timeout"      Search for keyword in the log
  %(prog)s --export r.csv --search "error"   Combined
        """
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        default="app.log",
        help="Path to the log file (default: app.log)"
    )
    
    parser.add_argument(
        "--export",
        type=str,
        default=None,
        metavar="FILENAME",
        help="Export the analysis summary to a CSV file"
    )
    
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        metavar="KEYWORD",
        help="Search for a keyword in the log file (case-insensitive)"
    )
    
    return parser.parse_args()


# ---------------------------------------------------------------------------
#  Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Main entry point for the Log File Analyzer.
    
    Workflow:
      1. Parse CLI arguments
      2. Read and validate the log file
      3. Count log levels
      4. Display summary
      5. Export to CSV if --export is provided
      6. Search for keyword if --search is provided
    """
    args = parse_arguments()
    
    print(f"\n[INFO] Analyzing log file: '{args.log_file}'\n")
    
    try:
        # Step 1: Read the log file (with validation)
        lines = read_log_file(args.log_file)
        
        # Step 2: Count log levels
        counts = count_log_levels(lines)
        
        # Step 3: Display the formatted summary
        display_summary(counts)
        
        # Step 4: Export to CSV (if requested)
        if args.export:
            export_to_csv(counts, args.export)
        
        # Step 5: Search for keyword (if requested)
        if args.search:
            results = search_keyword(lines, args.search)
            display_search_results(results, args.search)
        
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except IsADirectoryError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except PermissionError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"\n[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


# Allow the script to be run directly
if __name__ == "__main__":
    main()
