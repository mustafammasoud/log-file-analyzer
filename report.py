"""
Report Module
-------------
Provides the Report class responsible for:
  - Displaying a formatted analysis summary in the terminal (with colors).
  - Displaying the most common error messages.
  - Displaying execution time.
  - Saving the analysis results as report.json and report.csv.
"""

import csv
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class Report:
    """
    Generates and outputs analysis reports.

    Supports:
      - Color-coded terminal display with per-file breakdowns.
      - Display of most common ERROR/CRITICAL messages.
      - Display of execution time.
      - JSON export to report.json.
      - CSV export to report.csv.
    """

    # The display order for log levels
    LEVEL_ORDER = ["INFO", "WARNING", "ERROR", "CRITICAL"]

    # ANSI color codes for terminal output
    COLORS = {
        "INFO": "\033[94m",      # Blue
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "CRITICAL": "\033[95m",  # Magenta
        "HEADER": "\033[1;96m",  # Bold Cyan
        "BOLD": "\033[1m",
        "GREEN": "\033[92m",
        "RESET": "\033[0m",
    }

    def __init__(
        self,
        analysis_results: Dict,
        common_errors: Optional[List[Tuple[str, int]]] = None,
        execution_time: Optional[float] = None,
    ) -> None:
        """
        Initialize the report with analysis results.

        Args:
            analysis_results: Dictionary from LogAnalyzer.analyze_all()
                Expected structure:
                {
                    "per_file": { "filename.log": {...}, ... },
                    "total": {"INFO": ..., "WARNING": ..., ...}
                }
            common_errors: Optional list of (message, count) tuples from
                           LogAnalyzer.get_common_errors().
            execution_time: Optional execution time in seconds.
        """
        self.per_file: Dict[str, Dict[str, int]] = analysis_results.get("per_file", {})
        self.total: Dict[str, int] = analysis_results.get("total", {})
        self.common_errors: List[Tuple[str, int]] = common_errors or []
        self.execution_time: Optional[float] = execution_time
        self.timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _c(self, text: str, color: str) -> str:
        """
        Wrap text in an ANSI color code for terminal output.

        Args:
            text: The text to colorize.
            color: The color key from self.COLORS.

        Returns:
            Color-wrapped string (or plain text if color not found).
        """
        code = self.COLORS.get(color, "")
        reset = self.COLORS["RESET"]
        if not code:
            return text
        return f"{code}{text}{reset}"

    def display(self) -> None:
        """Print a color-coded, formatted summary to the terminal."""
        grand_total = sum(self.total.values())
        c = self._c  # shorthand

        # Header
        print(f"\n{c('=' * 56, 'HEADER')}")
        print(f"  {c('LOG FILE ANALYSIS REPORT', 'HEADER')}")
        print(f"{c('=' * 56, 'HEADER')}")

        # Execution time (if provided)
        if self.execution_time is not None:
            print(f"  Execution time: {c(f'{self.execution_time:.3f}s', 'GREEN')}")

        print(f"  Generated: {self.timestamp}")
        print(f"  Files analyzed: {len(self.per_file)}")

        # Date filter notice if present (can be set externally)
        if hasattr(self, 'date_filter') and self.date_filter:
            print(f"  {c('Date filter active', 'WARNING')}: {self.date_filter}")

        print(f"{c('=' * 56, 'HEADER')}")

        # --- Per-file breakdown ---
        for filename, counts in self.per_file.items():
            file_total = sum(counts.values())
            print(f"\n  {c('📄', 'BOLD')} {c(filename, 'BOLD')}")
            print("  " + "-" * 42)
            for level in self.LEVEL_ORDER:
                count = counts.get(level, 0)
                label = f"{level}:"
                colored_count = c(str(count), level) if count > 0 else str(count)
                print(f"    {c(label, level):<20} {colored_count}")
            print(f"    {'File Total:':<20} {c(str(file_total), 'GREEN')}")

        # --- Aggregate summary ---
        print(f"\n{c('-' * 56, 'HEADER')}")
        print(f"  {c('📊 AGGREGATE SUMMARY', 'BOLD')}")
        print("  " + "-" * 42)
        for level in self.LEVEL_ORDER:
            count = self.total.get(level, 0)
            label = f"{level}:"
            colored_count = c(str(count), level) if count > 0 else str(count)
            bar = self._progress_bar(count, grand_total) if grand_total > 0 else ""
            print(f"    {c(label, level):<15} {colored_count:<6} {bar}")
        print("  " + "-" * 42)
        print(f"    {'TOTAL:':<15} {c(str(grand_total), 'GREEN')}")
        print(f"{c('=' * 56, 'HEADER')}\n")

    def display_common_errors(self, top_n: int = 5) -> None:
        """
        Print the most common ERROR/CRITICAL messages to the terminal.

        Args:
            top_n: Number of top messages to display (default: 5).
        """
        if not self.common_errors:
            return

        c = self._c

        print(f"  {c('🔥 MOST COMMON ERRORS', 'BOLD')}")
        print("  " + "-" * 42)
        print(f"  {c('COUNT', 'ERROR'):<8} MESSAGE")
        print("  " + "-" * 42)
        for message, count in self.common_errors[:top_n]:
            colored_count = c(str(count), "ERROR")
            print(f"  {colored_count:<8} {message}")
        print("  " + "-" * 42 + "\n")

    @staticmethod
    def _progress_bar(count: int, total: int, width: int = 20) -> str:
        """
        Generate a simple text-based progress bar.

        Args:
            count: The count for a specific level.
            total: The grand total across all levels.
            width: Character width of the bar.

        Returns:
            String like "[####      ] 40%"
        """
        if total == 0:
            return ""

        fraction = count / total
        filled = int(fraction * width)
        bar = "#" * filled + " " * (width - filled)
        percent = int(fraction * 100)
        return f"[{bar}] {percent}%"

    def to_json(self, output_file: str = "report.json") -> None:
        """
        Save the analysis results as a JSON file.

        The JSON includes:
          - metadata (generated_at, files analyzed, execution time)
          - per-file breakdown
          - aggregate summary
          - common errors (if available)
          - grand total

        Args:
            output_file: Path for the output JSON file (default: report.json).

        Raises:
            IOError: If the file cannot be written.
        """
        report_data = {
            "report_metadata": {
                "generated_at": self.timestamp,
                "files_analyzed": list(self.per_file.keys()),
                "total_files": len(self.per_file),
            },
            "per_file_breakdown": {},
            "aggregate_summary": self.total,
            "grand_total": sum(self.total.values()),
        }

        if self.execution_time is not None:
            report_data["report_metadata"]["execution_time_seconds"] = round(
                self.execution_time, 3
            )

        # Format per-file breakdown with level ordering
        for filename, counts in self.per_file.items():
            ordered = {}
            for level in self.LEVEL_ORDER:
                ordered[level] = counts.get(level, 0)
            report_data["per_file_breakdown"][filename] = ordered

        # Add common errors if available
        if self.common_errors:
            report_data["common_errors"] = [
                {"message": msg, "count": cnt} for msg, cnt in self.common_errors
            ]

        try:
            with open(output_file, "w") as f:
                json.dump(report_data, f, indent=2)
            print(f"[INFO] Report saved to: '{output_file}'")
        except IOError as e:
            raise IOError(f"Failed to write report to '{output_file}': {e}")

    def to_csv(self, output_file: str = "report.csv") -> None:
        """
        Save the aggregate summary as a CSV file.

        Args:
            output_file: Path for the output CSV file (default: report.csv).

        Raises:
            IOError: If the file cannot be written.
        """
        try:
            with open(output_file, "w", newline="") as f:
                writer = csv.writer(f)

                # Header row
                writer.writerow(["Log Level", "Count"])

                # Data rows in standard order
                for level in self.LEVEL_ORDER:
                    writer.writerow([level, self.total.get(level, 0)])

                # Footer row with total
                writer.writerow(["TOTAL", sum(self.total.values())])

            print(f"[INFO] Report saved to: '{output_file}'")
        except IOError as e:
            raise IOError(f"Failed to write report to '{output_file}': {e}")
