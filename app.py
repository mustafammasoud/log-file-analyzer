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
import time

from flask import Flask, jsonify, render_template, request, send_file

from log_analyzer import LogAnalyzer

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# Store analysis results in memory for download endpoints
_latest_analysis: dict | None = None
_latest_common_errors: list | None = None
_latest_total: dict | None = None
_latest_per_file: dict | None = None


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has a .log extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "log"


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Home page: upload log files and display analysis results.
    """
    global _latest_analysis, _latest_common_errors, _latest_total, _latest_per_file

    if request.method == "POST":
        # Check if files were uploaded
        if "log_files" not in request.files:
            return render_template("index.html", error="No files uploaded.")

        files = request.files.getlist("log_files")
        uploaded_files = [f for f in files if f and f.filename and allowed_file(f.filename)]

        if not uploaded_files:
            return render_template(
                "index.html",
                error="No valid .log files uploaded. Please upload files with a .log extension.",
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
                return render_template(
                    "index.html",
                    error=f"Could not decode '{f.filename}'. Ensure it is a UTF-8 text file.",
                )
            except Exception as e:
                return render_template(
                    "index.html", error=f"Error reading '{f.filename}': {str(e)}"
                )

        if not file_contents:
            return render_template(
                "index.html", error="Uploaded files are empty or contain no readable content."
            )

        # Analyze using the existing LogAnalyzer
        start_time = time.perf_counter()
        analyzer = LogAnalyzer()
        analysis_results = analyzer.analyze_all(file_contents)
        common_errors = analyzer.get_common_errors(top_n=10)
        elapsed = round(time.perf_counter() - start_time, 3)

        # Store globally for download endpoints
        _latest_analysis = analysis_results
        _latest_common_errors = common_errors
        _latest_total = analysis_results.get("total", {})
        _latest_per_file = analysis_results.get("per_file", {})

        # Prepare data for the template
        total_logs = sum(_latest_total.values())
        files_analyzed = list(_latest_per_file.keys())

        # Per-file breakdown for table
        per_file_data = []
        for fname, counts in _latest_per_file.items():
            per_file_data.append(
                {
                    "name": fname,
                    "INFO": counts.get("INFO", 0),
                    "WARNING": counts.get("WARNING", 0),
                    "ERROR": counts.get("ERROR", 0),
                    "CRITICAL": counts.get("CRITICAL", 0),
                    "total": sum(counts.values()),
                }
            )

        return render_template(
            "index.html",
            analysis=analysis_results,
            total_logs=total_logs,
            level_counts=_latest_total,
            common_errors=common_errors,
            files_analyzed=files_analyzed,
            grand_total=total_logs,
            per_file_data=per_file_data,
            execution_time=elapsed,
        )

    return render_template("index.html")


@app.route("/download/json")
def download_json():
    """Download analysis results as JSON."""
    if not _latest_analysis:
        return jsonify({"error": "No analysis data available. Please upload log files first."}), 400

    report_data = {
        "report_metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "files_analyzed": list(_latest_per_file.keys()),
            "total_files": len(_latest_per_file),
        },
        "per_file_breakdown": _latest_per_file,
        "aggregate_summary": _latest_total,
        "grand_total": sum(_latest_total.values()),
    }

    if _latest_common_errors:
        report_data["common_errors"] = [
            {"message": msg, "count": cnt} for msg, cnt in _latest_common_errors
        ]

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
    """Download aggregate summary as CSV."""
    if not _latest_total:
        return jsonify({"error": "No analysis data available. Please upload log files first."}), 400

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Log Level", "Count"])
    for level in ["INFO", "WARNING", "ERROR", "CRITICAL"]:
        writer.writerow([level, _latest_total.get(level, 0)])
    writer.writerow(["TOTAL", sum(_latest_total.values())])

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
