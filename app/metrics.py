"""Bounded, thread-safe Prometheus metrics without runtime dependencies."""

from collections import defaultdict
from threading import Lock


BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
ROUTES = frozenset(("/", "/health", "/api/info", "/api/status", "/metrics"))
METHODS = frozenset(("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"))


class Metrics:
    def __init__(self):
        self._lock = Lock()
        self._requests = defaultdict(int)
        self._buckets = [0] * len(BUCKETS)
        self._count = 0
        self._sum = 0.0

    def observe(self, method, path, status, duration):
        # Never put arbitrary URLs, query strings, or methods into labels.
        route = path if path in ROUTES else "unknown"
        method = method if method in METHODS else "OTHER"
        with self._lock:
            self._requests[(method, route, str(int(status)))] += 1
            self._count += 1
            self._sum += duration
            for index, limit in enumerate(BUCKETS):
                if duration <= limit:
                    self._buckets[index] += 1

    def render(self, uptime):
        with self._lock:
            lines = [
                "# HELP service_status_uptime_seconds Seconds since process startup.",
                "# TYPE service_status_uptime_seconds gauge",
                f"service_status_uptime_seconds {uptime:.3f}",
                "# HELP service_status_http_requests_total Completed HTTP requests.",
                "# TYPE service_status_http_requests_total counter",
            ]
            for (method, route, status), count in sorted(self._requests.items()):
                lines.append(
                    f'service_status_http_requests_total{{method="{method}",route="{route}",status="{status}"}} {count}'
                )
            lines.extend([
                "# HELP service_status_http_request_duration_seconds Server request duration.",
                "# TYPE service_status_http_request_duration_seconds histogram",
            ])
            for limit, count in zip(BUCKETS, self._buckets):
                lines.append(f'service_status_http_request_duration_seconds_bucket{{le="{limit}"}} {count}')
            lines.extend([
                f'service_status_http_request_duration_seconds_bucket{{le="+Inf"}} {self._count}',
                f"service_status_http_request_duration_seconds_sum {self._sum:.9f}",
                f"service_status_http_request_duration_seconds_count {self._count}",
            ])
        return ("\n".join(lines) + "\n").encode("utf-8")
