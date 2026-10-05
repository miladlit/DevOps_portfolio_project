"""Check the application through real HTTP requests on a temporary port."""

import json
import threading
import unittest
from datetime import datetime
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.server import RequestHandler, StatusServer, main


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = StatusServer(("127.0.0.1", 0), RequestHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_health(self):
        with urlopen(self.base_url + "/health", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "application/json")
            self.assertEqual(json.load(response), {"status": "ok"})

    def test_info(self):
        with urlopen(self.base_url + "/api/info", timeout=5) as response:
            self.assertEqual(json.load(response), {"name": "Service Status", "version": "0.1.0"})

    def test_homepage(self):
        with urlopen(self.base_url + "/", timeout=5) as response:
            self.assertEqual(response.headers.get_content_type(), "text/html")
            self.assertIn(b"<h1>Service Status</h1>", response.read())

    def test_unknown_route(self):
        with self.assertRaises(HTTPError) as caught:
            urlopen(self.base_url + "/missing", timeout=5)
        with caught.exception as response:
            self.assertEqual(response.code, 404)
            self.assertEqual(json.load(response), {"error": "Not found"})

    def test_query_strings_do_not_change_api_routes(self):
        cases = {
            "/health?source=test": {"status": "ok"},
            "/api/info?source=test": {"name": "Service Status", "version": "0.1.0"},
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                with urlopen(self.base_url + path, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(json.load(response), expected)

    def test_repository_files_are_not_served(self):
        for path in ("/README.md", "/app/server.py", "/../README.md", "/%2e%2e/README.md"):
            with self.subTest(path=path):
                with self.assertRaises(HTTPError) as caught:
                    urlopen(self.base_url + path, timeout=5)
                with caught.exception as response:
                    self.assertEqual(response.code, 404)
                    self.assertEqual(response.headers.get_content_type(), "application/json")
                    self.assertEqual(json.load(response), {"error": "Not found"})

    def test_unsupported_method_does_not_break_health(self):
        request = Request(self.base_url + "/health", method="POST", data=b"")
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=5)
        with caught.exception as response:
            # BaseHTTPRequestHandler returns 501 for unimplemented methods.
            self.assertEqual(response.code, 501)
        with urlopen(self.base_url + "/health", timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.load(response), {"status": "ok"})

    def test_runtime_status(self):
        with patch("app.server.time.monotonic", return_value=self.server.started_monotonic + 125.5):
            with urlopen(self.base_url + "/api/status?source=test", timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "application/json")
                status = json.load(response)
        self.assertEqual(status["uptime_seconds"], 125.5)
        self.assertEqual(status["started_at"], self.server.started_at)
        self.assertIsNotNone(datetime.fromisoformat(status["started_at"]).tzinfo)

    def test_status_responses_are_not_cached(self):
        for path in ("/health", "/api/info", "/api/status"):
            with self.subTest(path=path):
                with urlopen(self.base_url + path, timeout=5) as response:
                    self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_head_matches_get_headers_without_body(self):
        with patch("app.server.time.monotonic", return_value=self.server.started_monotonic + 10):
            for path in ("/", "/health", "/api/info", "/api/status?source=test"):
                with self.subTest(path=path):
                    with urlopen(self.base_url + path, timeout=5) as response:
                        expected_headers = response.headers
                        expected_length = len(response.read())
                    request = Request(self.base_url + path, method="HEAD")
                    with urlopen(request, timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertEqual(response.read(), b"")
                        self.assertEqual(int(response.headers["Content-Length"]), expected_length)
                        for header in ("Content-Type", "Cache-Control"):
                            self.assertEqual(response.headers[header], expected_headers[header])

    def test_head_unknown_route(self):
        request = Request(self.base_url + "/missing", method="HEAD")
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=5)
        with caught.exception as response:
            self.assertEqual(response.code, 404)
            self.assertEqual(response.read(), b"")


class ConfigurationTests(unittest.TestCase):
    def test_default_and_custom_port(self):
        for environment, expected_port in (({}, 8000), ({"APP_PORT": "9000"}, 9000)):
            with self.subTest(environment=environment):
                with patch.dict("os.environ", environment, clear=True):
                    with patch("app.server.StatusServer") as server_class, patch("builtins.print"):
                        main()
                        server_class.assert_called_once_with(("127.0.0.1", expected_port), RequestHandler)
                        server_class.return_value.__enter__.return_value.serve_forever.assert_called_once()

    def test_invalid_port_fails_before_startup(self):
        for value in ("", "abc", "1.5", "0", "-1", "65536"):
            with self.subTest(value=value):
                with patch.dict("os.environ", {"APP_PORT": value}):
                    with patch("app.server.StatusServer") as server_class:
                        with self.assertRaisesRegex(SystemExit, "APP_PORT must be an integer between 1 and 65535"):
                            main()
                        server_class.assert_not_called()
