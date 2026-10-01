"""A small local HTTP server for the first project phase."""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


INDEX_FILE = Path(__file__).parent / "static" / "index.html"


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path

        if path == "/":
            self.send_body(200, INDEX_FILE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/info":
            self.send_json(200, {"name": "Service Status", "version": "0.1.0"})
        elif path == "/health":
            self.send_json(200, {"status": "ok"})
        else:
            self.send_json(404, {"error": "Not found"})

    def send_json(self, status, data):
        self.send_body(status, json.dumps(data).encode("utf-8"), "application/json")

    def send_body(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    host = os.environ.get("APP_HOST", "127.0.0.1")
    with ThreadingHTTPServer((host, 8000), RequestHandler) as server:
        print(f"Service Status is listening on {host}:8000", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
