# 📊 Log File Analyzer

A powerful yet lightweight **Python CLI tool** that reads application log files, analyzes message severity levels (`INFO`, `WARNING`, `ERROR`), and presents actionable insights — right in your terminal. Perfect for DevOps engineers, developers, and system administrators who need quick log analysis without heavy dependencies.

---

##  Features

- Log Level Analysis** — Automatically counts `INFO`, `WARNING`, and `ERROR` messages using intelligent regex parsing.
- CSV Export** — Save the analysis summary to a CSV file for reporting or further processing.
- Keyword Search** — Search for any keyword (case-insensitive) across all log lines, with line numbers and formatted output.
- Custom Log File Support** — Analyze any log file by specifying its path via `--log-file`.
- Robust Error Handling** — Gracefully handles missing files, empty files, directories, permission errors, and more.
- Clean & Modular Code** — Well-documented functions with type hints, docstrings, and logical separation of concerns.
- Zero External Dependencies** — Built entirely on Python's standard library — no `pip install` required.

---

##  Installation

### Prerequisites

- **Python 3.6+** (uses `argparse`, `csv`, `pathlib`, `re`, `typing` — all built-in)

### Steps

1. **Clone the repository** (or download the files):

```bash
git clone https://github.com/yourusername/log-file-analyzer.git
cd log-file-analyzer
```

2. **(Optional) Verify Python version:**

```bash
python3 --version
```

3. **Run the app:**

```bash
python3 app.py
```

> No additional dependencies to install. You're ready to go! 

---

##  Usage

### Basic Analysis

Analyze the default `app.log` file:

```bash
python3 app.py
```

### Search for a Keyword

Find every log line containing a specific word or phrase:

```bash
python3 analyzer.py --search "database"
python3 analyzer.py --search "timeout"
python3 analyzer.py --search "ERROR"
```

---

## 📋 Example Output

### Terminal Summary

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
```

### CSV Export (`report.csv`)

```
Log Level,Count
INFO,13
WARNING,4
ERROR,3
TOTAL,20
```

### Keyword Search

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
---

## 📁 Project Structure

```
log-file-analyzer/
├── app.py         
├── log_analyzer.py            
├── log_reader.py           
└── README.md        
```

---

## 🧩 Technologies Used

| Technology                                                                               | Purpose                                                              |
| ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| ![Python](https://img.shields.io/badge/Python-3.6%2B-3776AB?logo=python&logoColor=white) | Core programming language                                            |
| **`argparse`**                                                                           | Command-line argument parsing (`--log-file`, `--export`, `--search`) |
| **`csv`**                                                                                | Writing analysis results to CSV files                                |
| **`pathlib`**                                                                            | Cross-platform file path handling and validation                     |
| **`re`**                                                                                 | Regular expression matching for log level extraction                 |
| **`typing`**                                                                             | Type hints for better code clarity and IDE support                   |

> 100% standard library — **no external packages required**.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request for:

- Additional log format support
- New output formats (JSON, HTML, etc.)
- Performance improvements
- Bug fixes

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ using pure Python
</p>
