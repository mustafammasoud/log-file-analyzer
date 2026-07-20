"""
Log Analyzer Module
-------------------
Provides the LogAnalyzer class responsible for counting log levels
(INFO, WARNING, ERROR, CRITICAL) within log file lines using regex,
and extracting common error messages.
"""

import re
from collections import Counter
from typing import Dict, List, Tuple


class LogAnalyzer:
    """
    Analyzes log lines and counts occurrences of each severity level.

    Supports: INFO, WARNING, ERROR, CRITICAL
    Also extracts and ranks the most common ERROR/CRITICAL messages.
    """

    # The four standard log levels this analyzer tracks
    VALID_LEVELS = ["INFO", "WARNING", "ERROR", "CRITICAL"]

    # Regex pattern to extract log level from a standard log line
    # Matches format: YYYY-MM-DD HH:MM:SS LEVEL message
    LEVEL_PATTERN = re.compile(
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+'
        r'(INFO|WARNING|ERROR|CRITICAL)\b'
    )

    # Pattern to extract the full error message after the log level
    MESSAGE_PATTERN = re.compile(
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+'
        r'(?:ERROR|CRITICAL)\s+(.*)'
    )

    def __init__(self) -> None:
        """Initialize the analyzer with zeroed counters."""
        self.reset()

    def reset(self) -> None:
        """
        Reset all counters and error message store to zero.
        Useful when analyzing a new set of log files.
        """
        self._counts: Dict[str, int] = {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }
        self._error_messages: List[str] = []

    def analyze_lines(self, lines: List[str]) -> Dict[str, int]:
        """
        Analyze a list of log lines and count severity levels.

        Args:
            lines: List of log file lines (strings).

        Returns:
            Dictionary mapping log level -> count for THIS batch.
            Example: {"INFO": 5, "WARNING": 2, "ERROR": 1, "CRITICAL": 0}
        """
        batch_counts: Dict[str, int] = {
            "INFO": 0,
            "WARNING": 0,
            "ERROR": 0,
            "CRITICAL": 0,
        }

        for line in lines:
            if not line:
                continue

            match = self.LEVEL_PATTERN.search(line)
            if match:
                level = match.group(1)
                batch_counts[level] += 1

        return batch_counts

    def extract_error_messages(self, lines: List[str]) -> None:
        """
        Extract ERROR and CRITICAL message text from log lines and store them.

        Args:
            lines: List of log file lines to scan for error messages.
        """
        for line in lines:
            match = self.MESSAGE_PATTERN.search(line)
            if match:
                message = match.group(1).strip()
                if message:
                    self._error_messages.append(message)

    def get_common_errors(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """
        Get the most common ERROR/CRITICAL messages, ranked by frequency.

        Args:
            top_n: Number of top messages to return (default: 5).

        Returns:
            List of (message, count) tuples sorted by count descending.
            Example: [("timeout", 3), ("connection lost", 1), ...]
        """
        if not self._error_messages:
            return []

        counter = Counter(self._error_messages)
        return counter.most_common(top_n)

    def analyze_file(self, filename: str, lines: List[str]) -> Dict[str, int]:
        """
        Analyze a single file's lines and accumulate results.

        Args:
            filename: Name of the file (used for logging/display).
            lines: List of log lines from the file.

        Returns:
            Dictionary of counts for this specific file.
        """
        file_counts = self.analyze_lines(lines)

        # Extract error messages from this file
        self.extract_error_messages(lines)

        # Accumulate into the master counter
        for level in self.VALID_LEVELS:
            self._counts[level] += file_counts.get(level, 0)

        return file_counts

    def analyze_all(self, file_contents: Dict[str, List[str]]) -> Dict:
        """
        Analyze all loaded log files and aggregate results.

        Args:
            file_contents: Dictionary mapping filename -> list of lines.

        Returns:
            Nested dictionary:
            {
                "per_file": {
                    "app.log": {"INFO": ..., "WARNING": ..., ...},
                    ...
                },
                "total": {"INFO": ..., "WARNING": ..., ...}
            }
        """
        # Reset before starting fresh analysis
        self.reset()

        per_file: Dict[str, Dict[str, int]] = {}

        for filename, lines in file_contents.items():
            file_counts = self.analyze_file(filename, lines)
            per_file[filename] = file_counts

        # Return both per-file breakdown and the total aggregate
        return {
            "per_file": per_file,
            "total": dict(self._counts),
        }

    @property
    def counts(self) -> Dict[str, int]:
        """
        Get the current accumulated counts.

        Returns:
            Dictionary of total counts across all analyzed files.
        """
        return dict(self._counts)

    @property
    def total_count(self) -> int:
        """
        Get the total number of log entries analyzed.

        Returns:
            Sum of all level counts.
        """
        return sum(self._counts.values())
