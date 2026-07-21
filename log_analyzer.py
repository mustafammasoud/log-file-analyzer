"""
Log Analyzer Module
-------------------
Provides the LogAnalyzer class responsible for counting log levels
(DEBUG, INFO, WARNING, ERROR, CRITICAL) within log file lines using
regex, extracting common error messages (overall and per-file), and
building a time-bucketed timeline of events for charting.
"""

import re
from collections import Counter, OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class LogAnalyzer:
    """
    Analyzes log lines and counts occurrences of each severity level.

    Supports: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Also extracts and ranks the most common ERROR/CRITICAL messages,
    tracks which errors came from which file, and can bucket events
    into a timeline for charting.
    """

    # The five standard log levels this analyzer tracks
    VALID_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    # Regex pattern to extract log level from a standard log line
    # Matches format: YYYY-MM-DD HH:MM:SS LEVEL message
    # The level name may optionally be wrapped in brackets, e.g. "[INFO]"
    LEVEL_PATTERN = re.compile(
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+'
        r'\[?(DEBUG|INFO|WARNING|ERROR|CRITICAL)\b\]?'
    )

    # Pattern to extract the full error message after the log level
    # (also tolerates an optional "[LEVEL]" bracketed form)
    MESSAGE_PATTERN = re.compile(
        r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+'
        r'\[?(?:ERROR|CRITICAL)\b\]?\s+(.*)'
    )

    # Pattern to pull just the leading timestamp off a line (for the timeline)
    TIMESTAMP_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})')

    def __init__(self) -> None:
        """Initialize the analyzer with zeroed counters."""
        self.reset()

    def reset(self) -> None:
        """
        Reset all counters and error message store to zero.
        Useful when analyzing a new set of log files.
        """
        self._counts: Dict[str, int] = {level: 0 for level in self.VALID_LEVELS}
        self._error_messages: List[str] = []
        self._per_file_errors: Dict[str, List[str]] = {}

    def analyze_lines(self, lines: List[str]) -> Dict[str, int]:
        """
        Analyze a list of log lines and count severity levels.

        Args:
            lines: List of log file lines (strings).

        Returns:
            Dictionary mapping log level -> count for THIS batch.
            Example: {"DEBUG": 0, "INFO": 5, "WARNING": 2, "ERROR": 1, "CRITICAL": 0}
        """
        batch_counts: Dict[str, int] = {level: 0 for level in self.VALID_LEVELS}

        for line in lines:
            if not line:
                continue

            match = self.LEVEL_PATTERN.search(line)
            if match:
                level = match.group(1)
                batch_counts[level] += 1

        return batch_counts

    def extract_error_messages(self, lines: List[str]) -> List[str]:
        """
        Extract ERROR and CRITICAL message text from log lines, store them
        in the aggregate list, and also return the messages found in this
        batch (used to track errors per-file).

        Args:
            lines: List of log file lines to scan for error messages.

        Returns:
            List of error/critical messages found in this batch.
        """
        found: List[str] = []
        for line in lines:
            match = self.MESSAGE_PATTERN.search(line)
            if match:
                message = match.group(1).strip()
                if message:
                    found.append(message)

        self._error_messages.extend(found)
        return found

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

        # Extract error messages from this file (kept both aggregated and per-file)
        file_errors = self.extract_error_messages(lines)
        self._per_file_errors[filename] = file_errors

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
                    "app.log": {"DEBUG": ..., "INFO": ..., ...},
                    ...
                },
                "total": {"DEBUG": ..., "INFO": ..., ...},
                "per_file_errors": {
                    "app.log": ["error message 1", ...],
                    ...
                }
            }
        """
        # Reset before starting fresh analysis
        self.reset()

        per_file: Dict[str, Dict[str, int]] = {}

        for filename, lines in file_contents.items():
            file_counts = self.analyze_file(filename, lines)
            per_file[filename] = file_counts

        # Return per-file breakdown, the total aggregate, and per-file errors
        return {
            "per_file": per_file,
            "total": dict(self._counts),
            "per_file_errors": dict(self._per_file_errors),
        }

    def get_timeline(self, file_contents: Dict[str, List[str]]) -> Dict:
        """
        Build a time-bucketed timeline of events across all given files,
        suitable for feeding directly into a multi-series chart.

        The bucket size is chosen automatically based on how wide the
        log's time range is, so both a 10-minute log and a 2-week log
        produce a readable number of points:
          - span <= 3 hours   -> bucket every 5 minutes
          - span <= 48 hours  -> bucket every hour
          - otherwise         -> bucket every day

        Args:
            file_contents: Dictionary mapping filename -> list of lines.

        Returns:
            {
                "labels": ["08:00", "08:05", ...],
                "series": {"DEBUG": [...], "INFO": [...], "WARNING": [...],
                           "ERROR": [...], "CRITICAL": [...]}
            }
            Empty labels/series (all levels present with empty lists) if no
            timestamped lines were found.
        """
        entries: List[Tuple[datetime, str]] = []

        for lines in file_contents.values():
            for line in lines:
                ts_match = self.TIMESTAMP_PATTERN.match(line)
                if not ts_match:
                    continue
                lvl_match = self.LEVEL_PATTERN.search(line)
                if not lvl_match:
                    continue
                try:
                    dt = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                entries.append((dt, lvl_match.group(1)))

        if not entries:
            return {"labels": [], "series": {level: [] for level in self.VALID_LEVELS}}

        entries.sort(key=lambda e: e[0])
        start = entries[0][0]
        end = entries[-1][0]
        span_seconds = (end - start).total_seconds()

        if span_seconds <= 3 * 3600:
            bucket_seconds = 5 * 60
            label_fmt = "%H:%M"
        elif span_seconds <= 48 * 3600:
            bucket_seconds = 3600
            label_fmt = "%m-%d %H:00"
        else:
            bucket_seconds = 24 * 3600
            label_fmt = "%Y-%m-%d"

        buckets: "OrderedDict[str, Dict[str, int]]" = OrderedDict()

        for dt, level in entries:
            offset = (dt - start).total_seconds()
            bucket_index = int(offset // bucket_seconds)
            bucket_start = start + timedelta(seconds=bucket_index * bucket_seconds)
            label = bucket_start.strftime(label_fmt)
            if label not in buckets:
                buckets[label] = {lvl: 0 for lvl in self.VALID_LEVELS}
            buckets[label][level] += 1

        labels = list(buckets.keys())
        series = {lvl: [buckets[label][lvl] for label in labels] for lvl in self.VALID_LEVELS}

        return {"labels": labels, "series": series}

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
