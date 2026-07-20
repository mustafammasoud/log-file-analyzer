"""
Log Reader Module
-----------------
Provides the LogReader class responsible for discovering and reading
.log files from a specified directory.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Configure module logger
logger = logging.getLogger(__name__)


class LogReader:
    """
    Discovers and reads .log files from a given folder.

    Attributes:
        logs_dir (Path): Path to the directory containing log files.
    """

    # Pattern to extract the date from the beginning of a log line: YYYY-MM-DD
    DATE_PATTERN = re.compile(r'^(\d{4}-\d{2}-\d{2})')

    def __init__(self, logs_dir: str = "logs") -> None:
        """
        Initialize the LogReader with the path to the logs directory.

        Args:
            logs_dir: Relative or absolute path to the logs folder.
                      Defaults to "logs".
        """
        self.logs_dir = Path(logs_dir)

    def discover_log_files(self) -> List[Path]:
        """
        Scan the logs directory and return paths of all .log files.

        Returns:
            List of Path objects for each .log file found.

        Raises:
            FileNotFoundError: If the logs directory does not exist.
            ValueError: If no .log files are found in the directory.
        """
        # Check if the logs directory exists
        if not self.logs_dir.exists():
            raise FileNotFoundError(
                f"Logs directory not found: '{self.logs_dir}'"
            )

        if not self.logs_dir.is_dir():
            raise NotADirectoryError(
                f"Expected a directory, but '{self.logs_dir}' is not a folder"
            )

        # Collect all .log files
        log_files: List[Path] = sorted(self.logs_dir.glob("*.log"))

        if not log_files:
            raise ValueError(
                f"No .log files found in directory: '{self.logs_dir}'"
            )

        logger.info(f"Discovered {len(log_files)} log file(s) in '{self.logs_dir}'")
        return log_files

    def read_file(self, filepath: Path) -> List[str]:
        """
        Read a single .log file and return its non-empty lines.

        Performs validation:
          - File exists
          - File is not empty
          - File is readable

        Args:
            filepath: Path to the .log file.

        Returns:
            List of stripped, non-empty lines from the file.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is empty.
            PermissionError: If the file cannot be read.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: '{filepath}'")

        if filepath.stat().st_size == 0:
            raise ValueError(f"Log file is empty: '{filepath}'")

        try:
            with open(filepath, "r") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except PermissionError:
            raise PermissionError(f"Permission denied: cannot read '{filepath}'")
        except OSError as e:
            raise OSError(f"Error reading '{filepath}': {e}")

        if not lines:
            raise ValueError(f"Log file contains no content: '{filepath}'")

        logger.info(f"Read {len(lines)} lines from '{filepath.name}'")
        return lines

    def filter_by_date_range(
        self,
        lines: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[str]:
        """
        Filter log lines to only include entries within a date range.

        Args:
            lines: List of log lines to filter.
            start_date: Inclusive start date (format: YYYY-MM-DD). If None, no lower bound.
            end_date: Inclusive end date (format: YYYY-MM-DD). If None, no upper bound.

        Returns:
            Filtered list of lines whose dates fall within the range.

        Raises:
            ValueError: If a date string is provided in an invalid format.
        """
        if start_date is None and end_date is None:
            return lines  # No filtering needed

        parsed_start: Optional[datetime] = None
        parsed_end: Optional[datetime] = None

        if start_date is not None:
            try:
                parsed_start = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid start date format: '{start_date}'. Expected YYYY-MM-DD."
                )

        if end_date is not None:
            try:
                parsed_end = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid end date format: '{end_date}'. Expected YYYY-MM-DD."
                )

        filtered: List[str] = []

        for line in lines:
            match = self.DATE_PATTERN.match(line)
            if not match:
                # Lines without a date at the start are kept as-is
                filtered.append(line)
                continue

            try:
                line_date = datetime.strptime(match.group(1), "%Y-%m-%d")
            except ValueError:
                # If date can't be parsed, keep the line
                filtered.append(line)
                continue

            # Check lower bound
            if parsed_start is not None and line_date < parsed_start:
                continue
            # Check upper bound
            if parsed_end is not None and line_date > parsed_end:
                continue

            filtered.append(line)

        return filtered

    def read_all(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict:
        """
        Discover all .log files, optionally filter by date range, and read contents.

        Args:
            start_date: Optional inclusive start date filter (YYYY-MM-DD).
            end_date: Optional inclusive end date filter (YYYY-MM-DD).

        Returns:
            Dictionary mapping filename (str) -> list of lines (List[str]).
            Example: {"app.log": ["line1", "line2", ...]}

        Raises:
            FileNotFoundError: If the logs directory doesn't exist.
            ValueError: If date format is invalid or no .log files found.
        """
        # Validate date formats BEFORE reading any files (fatal if invalid)
        if start_date is not None:
            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid start date format: '{start_date}'. Expected YYYY-MM-DD."
                )

        if end_date is not None:
            try:
                datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Invalid end date format: '{end_date}'. Expected YYYY-MM-DD."
                )

        log_files = self.discover_log_files()
        file_contents: dict = {}

        for filepath in log_files:
            try:
                lines = self.read_file(filepath)

                # Apply optional date filtering
                lines = self.filter_by_date_range(lines, start_date, end_date)

                if lines:  # Only include files that have matching lines after filter
                    file_contents[filepath.name] = lines
            except (ValueError, PermissionError, OSError) as e:
                logger.warning(f"Skipping '{filepath.name}': {e}")
                print(f"[WARNING] Skipping '{filepath.name}': {e}")
                continue

        if not file_contents:
            raise ValueError("No log files could be read successfully.")

        return file_contents
