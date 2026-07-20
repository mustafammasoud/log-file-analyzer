# Log File Analyzer

A clean Python CLI tool that reads a log file (`app.log`) and analyzes the frequency of **INFO**, **WARNING**, and **ERROR** messages.

## Features

- Reads log files with timestamped entries (format: `YYYY-MM-DD HH:MM:SS LEVEL message`)
- Counts occurrences of INFO, WARNING, and ERROR levels
- Displays a neatly formatted summary table
- Clean, modular code with typed functions and docstrings
- Graceful error handling for missing files

## Project Structure

```
log-file-analyzer/
├── analyzer.py      # Main Python script
├── app.log          # Sample log file for testing
├── README.md        # Project documentation
```

## Requirements

- Python 3.6+ (uses `pathlib`, `typing`, `re` — all standard library)

## Usage

1. Navigate to the project directory:

```bash
   cd log-file-analyzer

```

2. Run the analyzer:

```bash
   python3 analyzer.py

```

### Expected Output

```
[INFO] Analyzing log file: app.log

========================================
         LOG FILE ANALYSIS SUMMARY
========================================
LEVEL           COUNT
-------------------------
INFO            13
WARNING         4
ERROR           3
-------------------------
TOTAL           20
========================================
```

## Functions

| Function                  | Description                                    |
| ------------------------- | ---------------------------------------------- |
| `read_log_file(filepath)` | Reads the log file and returns lines as a list |
| `count_log_levels(lines)` | Counts INFO, WARNING, ERROR using regex        |
| `display_summary(counts)` | Prints a formatted summary table               |
| `main()`                  | Orchestrates the analysis workflow             |

## Customization

To analyze your own log file, replace `app.log` with your file, or modify the `log_file` variable in `analyzer.py`.
