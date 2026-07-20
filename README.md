# Log File Analyzer

A clean Python CLI tool that reads log files and analyzes the frequency of **INFO**, **WARNING**, and **ERROR** messages. Supports exporting to CSV, searching for keywords, and analyzing custom log files.

## Features

- ✅ Reads log files with timestamped entries (format: `YYYY-MM-DD HH:MM:SS LEVEL message`)
- ✅ Counts occurrences of INFO, WARNING, and ERROR levels
- ✅ Displays a neatly formatted summary table in the terminal
- ✅ **Export analysis to CSV** — save results to a file
- ✅ **Search for keywords** — case-insensitive search with line numbers
- ✅ **Custom log file support** — analyze any log file via `--log-file`
- ✅ **Robust error handling** — validates file existence, readability, empty files, and permissions
- ✅ Clean, modular code with typed functions, docstrings, and section comments

## Project Structure

```
log-file-analyzer/
├── analyzer.py      # Main Python script
├── app.log          # Sample log file for testing
├── README.md        # Project documentation
```

## Requirements

- Python 3.6+ (uses only standard library modules: `argparse`, `csv`, `pathlib`, `re`, `typing`)

## Usage

### Basic Analysis

```bash
python3 analyzer.py
```

### Analyze a Custom Log File

```bash
python3 analyzer.py --log-file server.log
```

### Export Results to CSV

```bash
python3 analyzer.py --export report.csv
```

### Search for a Keyword

```bash
python3 analyzer.py --search "error"
python3 analyzer.py --search "timeout"
```

### Combine Options

```bash
python3 analyzer.py --export report.csv --search "warning"
```

### Expected Output

```
[INFO] Analyzing log file: 'app.log'

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
[INFO] Report exported to: 'report.csv'
```

### CSV Output Format

When exported, the CSV file (`report.csv`) looks like:

```csv
Log Level,Count
INFO,13
WARNING,4
ERROR,3
TOTAL,20
```

### Search Output Example

```
[INFO] Found 3 match(es) for keyword: 'error'

============================================================
LINE     CONTENT
============================================================
7        2025-01-15 08:00:10 ERROR Failed to connect to external API: timeout
11       2025-01-15 08:00:15 ERROR Database query failed: connection lost
17       2025-01-15 08:00:30 ERROR Unhandled exception in worker thread: KeyError
============================================================
```

## Functions

| Function                                   | Description                                                                 |
| ------------------------------------------ | --------------------------------------------------------------------------- |
| `read_log_file(filepath)`                  | Reads and validates the log file (checks existence, emptiness, permissions) |
| `count_log_levels(lines)`                  | Counts INFO, WARNING, ERROR using regex                                     |
| `display_summary(counts)`                  | Prints a formatted summary table to the terminal                            |
| `export_to_csv(counts, output_file)`       | Writes the analysis results to a CSV file                                   |
| `search_keyword(lines, keyword)`           | Searches for a keyword (case-insensitive) and returns matching lines        |
| `display_search_results(results, keyword)` | Prints search results in a readable format                                  |
| `parse_arguments()`                        | Parses CLI arguments (`--log-file`, `--export`, `--search`)                 |
| `main()`                                   | Orchestrates the full analysis workflow                                     |

## Error Handling

The tool gracefully handles these error scenarios:

| Scenario            | Message                                                   |
| ------------------- | --------------------------------------------------------- |
| File not found      | `[ERROR] Log file not found: 'nonexistent.log'`           |
| Path is a directory | `[ERROR] Expected a file, but 'logs' is a directory`      |
| Empty file          | `[ERROR] Log file is empty: 'empty.log'`                  |
| Permission denied   | `[ERROR] Permission denied: cannot read 'restricted.log'` |
