"""Verify operational log summaries and the command-line interface."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from app.log_report import summarize


ROOT = Path(__file__).resolve().parents[1]


def event(status=200, duration=0.1, route="/health", request_id="abc"):
    return json.dumps({"event": "http_request", "status": status,
                       "duration_seconds": duration, "route": route,
                       "request_id": request_id}) + "\n"


class LogReportTests(unittest.TestCase):
    def test_counts_error_rate_and_durations(self):
        report = summarize(iter([
            event(200, 0.1), event(404, 0.2, "unknown"), event(503, 0.6),
        ]))
        self.assertEqual(report["requests"], 3)
        self.assertEqual(report["errors"], 2)
        self.assertEqual(report["error_rate_percent"], 66.67)
        self.assertEqual(report["duration_seconds"], {"mean": 0.3, "max": 0.6})
        self.assertEqual(report["by_status"], {"200": 1, "404": 1, "503": 1})
        self.assertEqual(report["by_route"], {"/health": 2, "unknown": 1})

    def test_empty_input_has_no_latency_measurements(self):
        report = summarize(["\n", "   "])
        self.assertEqual(report["requests"], 0)
        self.assertEqual(report["error_rate_percent"], 0)
        self.assertEqual(report["duration_seconds"], {"mean": None, "max": None})

    def test_malformed_records_are_counted_without_echoing_input(self):
        bad = ["secret startup text", "null", "[]", event(True), event(600),
               event(duration=-1), event(duration=True), event(duration="0.1"),
               event(duration=float("nan")), event(duration=float("inf")),
               event(route=[]), '{"event":"http_request"}']
        report = summarize(bad + [event(), '{"event":"startup"}'])
        self.assertEqual(report["invalid_records"], len(bad))
        self.assertEqual(report["ignored_records"], 1)
        self.assertEqual(report["requests"], 1)
        self.assertNotIn("secret", json.dumps(report))

    def test_arbitrary_routes_are_grouped_without_exposing_them(self):
        report = summarize(event(route=f"/private/{index}?token=secret") for index in range(100))
        self.assertEqual(report["by_route"], {"unknown": 100})
        self.assertNotIn("secret", json.dumps(report))

    def test_exact_request_id_filter_and_older_logs(self):
        old = json.loads(event())
        del old["request_id"]
        lines = [event(request_id="abc"), event(request_id="abcd"), json.dumps(old)]
        report = summarize(lines, request_id="abc")
        self.assertEqual(report["requests"], 1)
        self.assertEqual(report["filtered_records"], 2)
        self.assertEqual(summarize(lines)["requests"], 3)
        self.assertEqual(summarize(lines, request_id="missing")["requests"], 0)

    def run_cli(self, *args, input=""):
        return subprocess.run([sys.executable, "-m", "app.log_report", *args],
                              cwd=ROOT, input=input, capture_output=True, text=True, timeout=5)

    def test_cli_reads_stdin_and_filters(self):
        result = self.run_cli("--request-id", "abc", input=event() + event(request_id="other"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["requests"], 1)
        self.assertEqual(result.stderr, "")

    def test_cli_reads_file_and_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requests.jsonl"
            path.write_text(event(500), encoding="utf-8")
            result = self.run_cli(str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["errors"], 1)
            result = self.run_cli(str(path.with_name("missing.jsonl")))
            self.assertEqual(result.returncode, 2)
            self.assertIn("Could not read log input", result.stderr)
            self.assertEqual(result.stdout, "")
