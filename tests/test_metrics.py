"""Check metric accounting, concurrency, and bounded labels."""

import json
import threading
import time
import unittest
from http import HTTPStatus
from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.metrics import Metrics
from app.server import RequestHandler, StatusServer


class MetricsTests(unittest.TestCase):
    def test_http_status_enums_use_numeric_labels(self):
        metrics = Metrics()
        metrics.observe("POST", "/health", HTTPStatus.NOT_IMPLEMENTED, 0.01)
        self.assertIn('status="501"} 1', metrics.render(0).decode())

    def test_cumulative_histogram_and_totals(self):
        metrics = Metrics()
        for duration in (0.001, 0.05, 6.0):
            metrics.observe("GET", "/health", 200, duration)
        output = metrics.render(42).decode()
        self.assertIn('route="/health",status="200"} 3', output)
        self.assertIn('bucket{le="0.005"} 1', output)
        self.assertIn('bucket{le="0.05"} 2', output)
        self.assertIn('bucket{le="+Inf"} 3', output)
        self.assertIn('seconds_sum 6.051000000', output)
        self.assertIn('uptime_seconds 42.000', output)
        self.assertTrue(output.endswith("\n"))

    def test_untrusted_paths_and_methods_have_bounded_labels(self):
        metrics = Metrics()
        for index in range(100):
            metrics.observe(f"CUSTOM{index}", f'/missing/{index}?token="secret"', 404, 0.1)
        output = metrics.render(0).decode()
        self.assertIn('method="OTHER",route="unknown",status="404"} 100', output)
        self.assertNotIn("secret", output)
        self.assertNotIn("CUSTOM", output)
        self.assertNotIn("/missing", output)

    def test_concurrent_requests_do_not_lose_counts(self):
        metrics = Metrics()
        def record(_):
            for _ in range(100):
                metrics.observe("GET", "/health", 200, 0.01)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(record, range(8)))
        self.assertIn('route="/health",status="200"} 800', metrics.render(0).decode())


class ObservabilityHTTPTests(unittest.TestCase):
    def test_http_metrics_errors_head_and_structured_logs(self):
        logs = StringIO()
        with patch("app.server.sys.stderr", logs):
            with StatusServer(("127.0.0.1", 0), RequestHandler) as server:
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/health?token=secret", timeout=5) as response:
                        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
                        response.read()
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(base + "/missing/private-value", timeout=5)
                    caught.exception.close()
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(Request(base + "/health", data=b"", method="POST"), timeout=5)
                    caught.exception.close()
                    # The handler records after writing the response; wait for it.
                    deadline = time.monotonic() + 5
                    while server.metrics._count < 3 and time.monotonic() < deadline:
                        time.sleep(0.01)
                    with urlopen(base + "/metrics", timeout=5) as response:
                        self.assertEqual(response.status, 200)
                        self.assertIn("version=0.0.4", response.headers["Content-Type"])
                        output = response.read().decode()
                    self.assertIn('method="GET",route="/health",status="200"} 1', output)
                    self.assertIn('route="unknown",status="404"} 1', output)
                    self.assertIn('method="POST",route="/health",status="501"} 1', output)
                    with urlopen(Request(base + "/metrics", method="HEAD"), timeout=5) as response:
                        self.assertEqual(response.read(), b"")
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
        records = [json.loads(line) for line in logs.getvalue().splitlines()]
        self.assertEqual(len(records), 5)
        self.assertEqual([record["status"] for record in records[:3]], [200, 404, 501])
        self.assertTrue(all(record["duration_seconds"] >= 0 for record in records))
        self.assertNotIn("secret", logs.getvalue())
        self.assertNotIn("private-value", logs.getvalue())
