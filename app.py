"""
Flask Dashboard for Log File Analyzer
--------------------------------------
Web interface to upload .log files, analyze log levels, display
charts via Chart.js, show top errors, and download reports.
"""

import csv
import io
import json
import os
import threading
import time
import uuid

from flask import Flask, redirect, render_template, request, send_file, session, url_for

from log_analyzer import LogAnalyzer
from log_reader import LogReader

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# ----------------------------------------------------------------------
# Per-user analysis store.
#
# Results used to live in plain module-level globals, which meant every
# visitor to the app shared the SAME data — if two people used the server
# at the same time, one could see (or download) the other's analysis.
#
# Instead, each visitor gets a random session id (stored in their signed
# session cookie). Their analysis results are kept server-side in this
# dict, keyed by that id, so uploads and downloads only ever touch data
# that belongs to the same browser session. Entries older than TTL are
# pruned so memory doesn't grow forever on a long-running server.
# ----------------------------------------------------------------------
_analysis_store: dict[str, dict] = {}
_store_lock = threading.Lock()
_STORE_TTL_SECONDS = 60 * 60  # 1 hour


def _get_session_id() -> str:
    """Get (or create) a unique id for the current visitor's browser session."""
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return session["sid"]


def _cleanup_store() -> None:
    """Drop analysis entries older than the TTL to bound memory usage."""
    cutoff = time.time() - _STORE_TTL_SECONDS
    with _store_lock:
        expired = [sid for sid, entry in _analysis_store.items() if entry["timestamp"] < cutoff]
        for sid in expired:
            del _analysis_store[sid]


def _save_analysis(sid: str, analysis_results: dict, common_errors: list, timeline: dict, comparison: dict | None) -> None:
    """Store one visitor's analysis results, replacing any previous result for them."""
    with _store_lock:
        _analysis_store[sid] = {
            "analysis": analysis_results,
            "common_errors": common_errors,
            "total": analysis_results.get("total", {}),
            "per_file": analysis_results.get("per_file", {}),
            "timeline": timeline,
            "comparison": comparison,
            "timestamp": time.time(),
        }


def _get_analysis(sid: str) -> dict | None:
    """Fetch one visitor's stored analysis results, if any."""
    with _store_lock:
        return _analysis_store.get(sid)


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has a .log extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "log"


def _build_comparison(per_file: dict, per_file_errors: dict) -> dict | None:
    """
    When exactly two files were analyzed together, build a side-by-side
    comparison: the per-level count delta, and error messages unique to
    each file. Returns None when the condition doesn't apply (not exactly
    two files), so the UI can simply skip the comparison section.
    """
    filenames = list(per_file.keys())
    if len(filenames) != 2:
        return None

    file1, file2 = filenames
    level_diff = {
        level: per_file[file2].get(level, 0) - per_file[file1].get(level, 0)
        for level in LogAnalyzer.VALID_LEVELS
    }

    errors1 = set(per_file_errors.get(file1, []))
    errors2 = set(per_file_errors.get(file2, []))

    return {
        "file1": file1,
        "file2": file2,
        "level_diff": level_diff,
        "only_in_file1": sorted(errors1 - errors2)[:10],
        "only_in_file2": sorted(errors2 - errors1)[:10],
    }


def _render_error(error: str, start_date: str = "", end_date: str = "", keyword: str = ""):
    """Re-render the upload page with an error message while preserving filter inputs."""
    return render_template(
        "index.html",
        error=error,
        start_date=start_date,
        end_date=end_date,
        keyword=keyword,
    )


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Home page: upload log files and display analysis results.
    Supports optional date-range and keyword filters applied before analysis.
    """
    _cleanup_store()
    sid = _get_session_id()

    if request.method == "POST":
        # Read optional filters (blank strings become None)
        start_date = (request.form.get("start_date") or "").strip()
        end_date = (request.form.get("end_date") or "").strip()
        keyword = (request.form.get("keyword") or "").strip()

        # Check if files were uploaded
        if "log_files" not in request.files:
            return _render_error("No files uploaded.", start_date, end_date, keyword)

        files = request.files.getlist("log_files")
        uploaded_files = [f for f in files if f and f.filename and allowed_file(f.filename)]

        if not uploaded_files:
            return _render_error(
                "No valid .log files uploaded. Please upload files with a .log extension.",
                start_date, end_date, keyword,
            )

        # Read uploaded files into memory
        file_contents = {}
        for f in uploaded_files:
            try:
                content = f.read().decode("utf-8")
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                if lines:
                    file_contents[f.filename] = lines
            except UnicodeDecodeError:
                return _render_error(
                    f"Could not decode '{f.filename}'. Ensure it is a UTF-8 text file.",
                    start_date, end_date, keyword,
                )
            except Exception as e:
                return _render_error(
                    f"Error reading '{f.filename}': {str(e)}", start_date, end_date, keyword
                )

        if not file_contents:
            return _render_error(
                "Uploaded files are empty or contain no readable content.",
                start_date, end_date, keyword,
            )

        # ------------------------------------------------------------
        # Apply optional date-range filter (reuses LogReader's logic)
        # ------------------------------------------------------------
        reader = LogReader()
        if start_date or end_date:
            try:
                for fname in list(file_contents.keys()):
                    filtered = reader.filter_by_date_range(
                        file_contents[fname],
                        start_date or None,
                        end_date or None,
                    )
                    if filtered:
                        file_contents[fname] = filtered
                    else:
                        del file_contents[fname]
            except ValueError as e:
                return _render_error(str(e), start_date, end_date, keyword)

        # ------------------------------------------------------------
        # Apply optional keyword filter (case-insensitive substring match)
        # ------------------------------------------------------------
        if keyword:
            keyword_lower = keyword.lower()
            for fname in list(file_contents.keys()):
                filtered = [line for line in file_contents[fname] if keyword_lower in line.lower()]
                if filtered:
                    file_contents[fname] = filtered
                else:
                    del file_contents[fname]

        if not file_contents:
            return _render_error(
                "No log entries match the selected filters. Try widening the date range or keyword.",
                start_date, end_date, keyword,
            )

        # Analyze using the existing LogAnalyzer
        start_time = time.perf_counter()
        analyzer = LogAnalyzer()
        analysis_results = analyzer.analyze_all(file_contents)
        common_errors = analyzer.get_common_errors(top_n=10)
        timeline = analyzer.get_timeline(file_contents)
        elapsed = round(time.perf_counter() - start_time, 3)

        total = analysis_results.get("total", {})
        per_file = analysis_results.get("per_file", {})
        per_file_errors = analysis_results.get("per_file_errors", {})

        # If exactly two files were uploaded together, build a diff summary
        comparison = _build_comparison(per_file, per_file_errors)

        # Store results for THIS visitor only (keyed by their session id)
        _save_analysis(sid, analysis_results, common_errors, timeline, comparison)

        # Prepare data for the template
        total_logs = sum(total.values())
        files_analyzed = list(per_file.keys())

        # Per-file breakdown for table
        per_file_data = []
        for fname, counts in per_file.items():
            per_file_data.append(
                {
                    "name": fname,
                    "DEBUG": counts.get("DEBUG", 0),
                    "INFO": counts.get("INFO", 0),
                    "WARNING": counts.get("WARNING", 0),
                    "ERROR": counts.get("ERROR", 0),
                    "CRITICAL": counts.get("CRITICAL", 0),
                    "total": sum(counts.values()),
                }
            )

        # Build a human-readable summary of applied filters (shown in the UI)
        filter_parts = []
        if start_date:
            filter_parts.append(f"from {start_date}")
        if end_date:
            filter_parts.append(f"to {end_date}")
        if keyword:
            filter_parts.append(f"containing '{keyword}'")
        filter_summary = " ".join(filter_parts) if filter_parts else ""

        return render_template(
            "index.html",
            analysis=analysis_results,
            total_logs=total_logs,
            level_counts=total,
            common_errors=common_errors,
            files_analyzed=files_analyzed,
            grand_total=total_logs,
            per_file_data=per_file_data,
            execution_time=elapsed,
            start_date=start_date,
            end_date=end_date,
            keyword=keyword,
            filter_summary=filter_summary,
            timeline=timeline,
            comparison=comparison,
        )

    # GET request: allow an error to be passed via query string (used by the
    # download endpoints when no analysis data is available yet)
    error = request.args.get("error")
    return render_template("index.html", error=error)


@app.route("/download/json")
def download_json():
    """Download the current visitor's analysis results as JSON."""
    _cleanup_store()
    entry = _get_analysis(session.get("sid", ""))
    if not entry:
        return redirect(url_for("index", error="No analysis data available. Please upload log files first."))

    per_file = entry["per_file"]
    total = entry["total"]
    common_errors = entry["common_errors"]
    timeline = entry.get("timeline")
    comparison = entry.get("comparison")

    report_data = {
        "report_metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files_analyzed": list(per_file.keys()),
            "total_files": len(per_file),
        },
        "per_file_breakdown": per_file,
        "aggregate_summary": total,
        "grand_total": sum(total.values()),
    }

    if common_errors:
        report_data["common_errors"] = [
            {"message": msg, "count": cnt} for msg, cnt in common_errors
        ]

    if timeline and timeline.get("labels"):
        report_data["timeline"] = timeline

    if comparison:
        report_data["comparison"] = comparison

    json_str = json.dumps(report_data, indent=2)
    mem_file = io.BytesIO(json_str.encode("utf-8"))
    mem_file.seek(0)

    return send_file(
        mem_file,
        mimetype="application/json",
        as_attachment=True,
        download_name="report.json",
    )


@app.route("/download/csv")
def download_csv():
    """Download the current visitor's aggregate summary as CSV."""
    _cleanup_store()
    entry = _get_analysis(session.get("sid", ""))
    if not entry:
        return redirect(url_for("index", error="No analysis data available. Please upload log files first."))

    total = entry["total"]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log Level", "Count"])
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        writer.writerow([level, total.get(level, 0)])
    writer.writerow(["TOTAL", sum(total.values())])

    mem_file = io.BytesIO(output.getvalue().encode("utf-8"))
    mem_file.seek(0)

    return send_file(
        mem_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name="report.csv",
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
