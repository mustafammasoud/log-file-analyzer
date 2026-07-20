# Log File Analyzer - Refactor Plan

- [x] Create `logs/` folder and move/populate `.log` files
- [x] Create `log_reader.py` - LogReader class (discover & read .log files)
- [x] Create `log_analyzer.py` - LogAnalyzer class (count INFO/WARNING/ERROR/CRITICAL)
- [x] Create `report.py` - Report class (formatted display + report.json export)
- [x] Rewrite `analyzer.py` - clean CLI entry point with argparse
- [x] Update `.gitignore` (ignore report.json, **pycache**, etc.)
- [x] Test everything ✅

## Test Results

| Test                                         | Result                                              |
| -------------------------------------------- | --------------------------------------------------- |
| `python3 analyzer.py`                        | ✅ 2 files analyzed, correct counts, JSON saved     |
| `python3 analyzer.py --no-json`              | ✅ Display only, no JSON file created               |
| `python3 analyzer.py --logs-dir nonexistent` | ✅ `[ERROR] Logs directory not found` + exit 1      |
| `report.json`                                | ✅ Correct JSON structure with per-file + aggregate |
