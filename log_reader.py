"""
Log Reader Module
-----------------
Provides the LogReader class responsible for discovering and reading
.log files from a specified directory.
"""

import logging
from pathlib import Path
from typing import List

# Configure module logger
logger = logging.getLogger(__name__)


class LogReader:
    """
    Discovers and reads .log files from a given folder.

    Attributes:
        logs_dir (Path): Path to the directory containing log files.
    """

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

    def read_all(self) -> dict:
        """
        Discover all .log files and read their contents.

        Returns:
            Dictionary mapping filename (str) -> list of lines (List[str]).
            Example: {"app.log": ["line1", "line2", ...]}

        Raises:
            FileNotFoundError: If the logs directory doesn't exist.
            ValueError: If no .log files found.
        """
        log_files = self.discover_log_files()
        file_contents: dict = {}

        for filepath in log_files:
            try:
                lines = self.read_file(filepath)
                file_contents[filepath.name] = lines
            except (ValueError, PermissionError, OSError) as e:
                logger.warning(f"Skipping '{filepath.name}': {e}")
                print(f"[WARNING] Skipping '{filepath.name}': {e}")
                continue

        if not file_contents:
            raise ValueError("No log files could be read successfully.")

        return file_contents
