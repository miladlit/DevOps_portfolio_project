"""Exercise the operational check against real successful and failing responses."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import threading
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check.sh"


@unittest.skipUnless(shutil.which("curl") and shutil.which("bash"), "requires curl and Bash")
class HealthCheckTests(unittest.TestCase):
    def check_response(self, status, body):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(status)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                return subprocess.run(
                    ["bash", str(SCRIPT), f"http://127.0.0.1:{server.server_port}/"],
                    cwd="/tmp", capture_output=True, text=True, timeout=10,
                )
            finally:
                server.shutdown()
                thread.join()

    def test_healthy_response(self):
        result = self.check_response(200, b'{"status": "ok"}')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Health check passed", result.stdout)

    def test_http_failure_even_with_healthy_body(self):
        result = self.check_response(503, b'{"status": "ok"}')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Health check passed", result.stdout)

    def test_invalid_json(self):
        result = self.check_response(200, b"not json")
        self.assertNotEqual(result.returncode, 0)

    def test_unhealthy_payload(self):
        result = self.check_response(200, b'{"status": "down"}')
        self.assertNotEqual(result.returncode, 0)
