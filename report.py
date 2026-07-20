"""
Report Module
-------------
Provides the Report class responsible for:
  - Displaying a formatted analysis summary in the terminal.
  - Saving the analysis results as report.json.
"""

import json
from datetime import datetime
from typing import Dict, List


class Report:
    """
    Generates and outputs analysis reports.

    Supports:
      - Formatted terminal display with per-file breakdowns.
      - JSON export to report.json.
    """

    # The display order for log levels
    LEVEL_ORDER = ["INFO", "WARNING", "ERROR", "CRITICAL"]

    def __init__(self, analysis_results: Dict) -> None:
        """
        Initialize the report with analysis results.

        Args:
            analysis_results: Dictionary from LogAnalyzer.analyze_all()
                Expected structure:
                {
                    "per_file": { "filename.log": {...}, ... },
                    "total": {"INFO": ..., "WARNING": ..., ...}
                }
        """
        self.per_file: Dict[str, Dict[str, int]] = analysis_results.get("per_file", {})
        self.total: Dict[str, int] = analysis_results.get("total", {})
        self.timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def display(self) -> None:
        """Print a formatted summary to the terminal."""
        grand_total = sum(self.total.values())

        print("\n" + "=" * 56)
        print("         LOG FILE ANALYSIS REPORT")
        print("=" * 56)
        print(f"  Generated: {self.timestamp}")
        print(f"  Files analyzed: {len(self.per_file)}")
        print("=" * 56)

        # --- Per-file breakdown ---
        for filename, counts in self.per_file.items():
            file_total = sum(counts.values())
            print(f"\n  📄 {filename}")
            print("  " + "-" * 42)
            for level in self.LEVEL_ORDER:
                count = counts.get(level, 0)
                label = f"{level}:"
                print(f"    {label:<12} {count}")
            print(f"    {'File Total:':<12} {file_total}")

        # --- Aggregate summary ---
        print("\n" + "-" * 56)
        print("  📊 AGGREGATE SUMMARY")
        print("  " + "-" * 42)
        for level in self.LEVEL_ORDER:
            count = self.total.get(level, 0)
            label = f"{level}:"
            bar = self._progress_bar(count, grand_total) if grand_total > 0 else ""
            print(f"    {label:<12} {count:<6} {bar}")
        print("  " + "-" * 42)
        print(f"    {'TOTAL:':<12} {grand_total}")
        print("=" * 56 + "\n")

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
            "per_file_breakdown": self.per_file,
            "aggregate_summary": self.total,
            "grand_total": sum(self.total.values()),
        }

        try:
            with open(output_file, "w") as f:
                json.dump(report_data, f, indent=2)
            print(f"[INFO] Report saved to: '{output_file}'")
        except IOError as e:
            raise IOError(f"Failed to write report to '{output_file}': {e}")
