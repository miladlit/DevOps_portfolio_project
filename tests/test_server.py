"""Check the application through real HTTP requests on a temporary port."""

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.server import RequestHandler


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), RequestHandler)
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
