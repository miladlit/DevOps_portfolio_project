"""A small local HTTP server for the first project phase."""

import json
import os
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from app.metrics import Metrics, ROUTES


INDEX_FILE = Path(__file__).parent / "static" / "index.html"


class StatusServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.started_monotonic = time.monotonic()
        self.metrics = Metrics()


class RequestHandler(BaseHTTPRequestHandler):
    def handle_one_request(self):
        self._request_started = time.monotonic()
        self._response_status = None
        try:
            super().handle_one_request()
        finally:
            if self._response_status is not None:
                duration = max(0, time.monotonic() - self._request_started)
                try:
                    path = urlsplit(self.path).path
                except ValueError:
                    path = "unknown"
                self.server.metrics.observe(self.command, path, self._response_status, duration)
                # Avoid query strings, client identifiers and arbitrary paths in logs.
                print(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event": "http_request",
                    "method": self.command,
                    "route": path if path in ROUTES else "unknown",
                    "status": self._response_status,
                    "duration_seconds": round(duration, 6),
                }), file=sys.stderr, flush=True)

    def send_response(self, code, message=None):
        self._response_status = code
        super().send_response(code, message)

    def log_message(self, format, *args):
        # One structured record is emitted after each request instead.
        pass

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self.send_json(400, {"error": "Invalid request path"})
            return

        if path == "/":
            self.send_body(200, INDEX_FILE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/info":
            self.send_json(200, {"name": "Service Status", "version": "0.1.0"})
        elif path == "/api/status":
            self.send_json(200, {
                "started_at": self.server.started_at,
                "uptime_seconds": round(time.monotonic() - self.server.started_monotonic, 3),
            })
        elif path == "/health":
            self.send_json(200, {"status": "ok"})
        elif path == "/metrics":
            self.send_body(200, self.server.metrics.render(
                time.monotonic() - self.server.started_monotonic
            ), "text/plain; version=0.0.4; charset=utf-8")
        else:
            self.send_json(404, {"error": "Not found"})

    def do_HEAD(self):
        self.do_GET()

    def send_json(self, status, data):
        self.send_body(status, json.dumps(data).encode("utf-8"), "application/json")

    def send_body(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def main():
    host = os.environ.get("APP_HOST", "127.0.0.1")
    try:
        port = int(os.environ.get("APP_PORT", "8000"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise SystemExit("APP_PORT must be an integer between 1 and 65535.") from None
    with StatusServer((host, port), RequestHandler) as server:
        print(f"Service Status is listening on {host}:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
