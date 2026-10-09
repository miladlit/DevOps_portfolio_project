"""Verify the repository's proxy site using an isolated, unprivileged Nginx."""

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.server import RequestHandler, StatusServer


ROOT = Path(__file__).resolve().parents[1]
NGINX = shutil.which(os.environ.get("NGINX_BINARY", "nginx"))


@unittest.skipUnless(NGINX, "requires Nginx; set NGINX_BINARY to its executable")
class ProxyTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="service-status-proxy-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.server = StatusServer(("127.0.0.1", 0), RequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_upstream)
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        self.url = f"http://127.0.0.1:{port}"
        site = (ROOT / "deploy/nginx/service-status.conf").read_text()
        site = site.replace("127.0.0.1:8080", f"127.0.0.1:{port}")
        site = site.replace("127.0.0.1:8000", f"127.0.0.1:{self.server.server_port}")
        site = site.replace("/var/log/nginx/", str(self.directory) + "/")
        config = self.directory / "nginx.conf"
        config.write_text(
            "daemon off; master_process off;\n"
            f"pid {self.directory}/nginx.pid;\n"
            f"error_log {self.directory}/main-error.log;\n"
            "events {}\nhttp {\n"
            + "".join(
                f"{kind}_temp_path {self.directory}/{kind};\n"
                for kind in ("client_body", "proxy", "fastcgi", "uwsgi", "scgi")
            )
            + site + "\n}\n"
        )
        command = [NGINX, "-e", "stderr", "-p", str(self.directory), "-c", str(config)]
        validation = subprocess.run(command + ["-t"], capture_output=True, text=True, timeout=10)
        self.assertEqual(validation.returncode, 0, validation.stderr)
        self.process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self.addCleanup(self.stop_proxy)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                self.fail(self.process.stderr.read().decode())
            try:
                with urlopen(self.url + "/health", timeout=1):
                    return
            except URLError:
                time.sleep(0.05)
        self.fail("Nginx did not become ready within five seconds")

    def stop_upstream(self):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=5)
            self.server = None

    def stop_proxy(self):
        if self.process.poll() is None:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.process.stderr.close()

    def test_routes_headers_and_head(self):
        with urlopen(self.url + "/health?source=proxy", timeout=5) as response:
            self.assertEqual(json.load(response), {"status": "ok"})
            self.assertEqual(response.headers["Cache-Control"], "no-store")
        with urlopen(self.url + "/", timeout=5) as response:
            self.assertIn(b"<h1>Service Status</h1>", response.read())
        with urlopen(Request(self.url + "/health", method="HEAD"), timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"")
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.url + "/missing", timeout=5)
        with caught.exception as response:
            self.assertEqual(response.code, 404)
            self.assertEqual(json.load(response), {"error": "Not found"})

    def test_stopped_upstream_returns_bad_gateway(self):
        self.stop_upstream()
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.url + "/health", timeout=5)
        with caught.exception as response:
            self.assertEqual(response.code, 502)
        log = (self.directory / "service-status-error.log").read_text()
        self.assertIn("upstream", log)
