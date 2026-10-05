"""A small local HTTP server for the first project phase."""

import json
import os
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


INDEX_FILE = Path(__file__).parent / "static" / "index.html"


class StatusServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class):
        super().__init__(server_address, handler_class)
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.started_monotonic = time.monotonic()


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path

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
