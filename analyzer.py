#!/usr/bin/env python3
"""
Log File Analyzer
-----------------
A CLI tool that reads app.log, counts INFO/WARNING/ERROR messages,
and displays a formatted summary.

Usage:
    python3 analyzer.py
"""

import re
import sys
from pathlib import Path
from typing import Dict, List


def read_log_file(filepath: str) -> List[str]:
    """
    Reads the log file and returns its lines as a list.
    
    Args:
        filepath: Path to the log file (e.g., "app.log")
    
    Returns:
        List of stripped lines from the file
    
    Raises:
        FileNotFoundError: If the log file doesn't exist
    """
    path = Path(filepath)
    
    # Check if file exists before attempting to read
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {filepath}")
    
    # Read all lines and strip trailing whitespace
    with open(path, 'r') as f:
        lines = [line.strip() for line in f.readlines()]
    
    return lines


def count_log_levels(lines: List[str]) -> Dict[str, int]:
    """
    Counts occurrences of each log level (INFO, WARNING, ERROR).
    
    Uses regex to find log level patterns at the start of log entries.
    
    Args:
        lines: List of log file lines
    
    Returns:
        Dictionary mapping log level -> count
    """
    # Initialize counters for the three required levels
    counts = {
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0,
    }
    
    # Pattern: looks for log level that appears after a timestamp pattern
    # Example: "2025-01-15 10:30:45 INFO Application started"
    pattern = re.compile(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+(INFO|WARNING|ERROR)\b')
    
    for line in lines:
        # Skip empty lines
        if not line:
            continue
        
        # Try to match the log level pattern
        match = pattern.search(line)
        if match:
            level = match.group(1)
            counts[level] += 1
    
    return counts


def display_summary(counts: Dict[str, int]) -> None:
    """
    Prints a formatted summary table of log level counts.
    
    Args:
        counts: Dictionary with log level counts (from count_log_levels)
    """
    # Calculate total for summary footer
    total = sum(counts.values())
    
    # Header
    print("=" * 40)
    print("         LOG FILE ANALYSIS SUMMARY")
    print("=" * 40)
    
    # Table header
    print(f"{'LEVEL':<15} {'COUNT':<10}")
    print("-" * 25)
    
    # Table rows - display in a fixed order for consistency
    for level in ["INFO", "WARNING", "ERROR"]:
        count = counts.get(level, 0)
        print(f"{level:<15} {count:<10}")
    
    # Summary footer
    print("-" * 25)
    print(f"{'TOTAL':<15} {total:<10}")
    print("=" * 40)


def main() -> None:
    """
    Main entry point for the Log File Analyzer.
    
    Orchestrates the workflow:
    1. Read the log file
    2. Count log levels
    3. Display the formatted summary
    """
    log_file = "app.log"
    
    print(f"\n[INFO] Analyzing log file: {log_file}\n")
    
    try:
        # Step 1: Read the log file
        lines = read_log_file(log_file)
        
        # Step 2: Count log levels
        counts = count_log_levels(lines)
        
        # Step 3: Display the summary
        display_summary(counts)
        
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


# Allow the script to be run directly
if __name__ == "__main__":
    main()
