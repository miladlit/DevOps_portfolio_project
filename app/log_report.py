"""Summarize JSONL request logs without runtime dependencies."""

import argparse
from collections import Counter
import json
import math
import sys

from app.metrics import ROUTES


def summarize(lines, request_id=None):
    statuses = Counter()
    routes = Counter()
    invalid = ignored = filtered = count = errors = 0
    mean = maximum = 0.0
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            invalid += 1
            continue
        if not isinstance(event, dict):
            invalid += 1
            continue
        if event.get("event") != "http_request":
            ignored += 1
            continue
        status = event.get("status")
        duration = event.get("duration_seconds")
        route = event.get("route")
        try:
            valid_duration = (type(duration) in (int, float)
                              and math.isfinite(duration) and duration >= 0)
        except OverflowError:
            valid_duration = False
        if (type(status) is not int or not 100 <= status <= 599
                or not valid_duration or not isinstance(route, str)):
            invalid += 1
            continue
        if request_id is not None and event.get("request_id") != request_id:
            filtered += 1
            continue
        count += 1
        errors += status >= 400
        mean += (duration - mean) / count
        maximum = max(maximum, duration)
        statuses[str(status)] += 1
        routes[route if route in ROUTES else "unknown"] += 1
    return {
        "requests": count,
        "errors": errors,
        "error_rate_percent": round(100 * errors / count, 2) if count else 0.0,
        "duration_seconds": {
            "mean": round(mean, 6) if count else None,
            "max": maximum if count else None,
        },
        "by_status": dict(sorted(statuses.items())),
        "by_route": dict(sorted(routes.items())),
        "invalid_records": invalid,
        "ignored_records": ignored,
        "filtered_records": filtered,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="JSONL file, or - for stdin (default)")
    parser.add_argument("--request-id", help="include only requests with this exact ID")
    args = parser.parse_args(argv)
    try:
        if args.file == "-":
            report = summarize(sys.stdin, args.request_id)
        else:
            with open(args.file, encoding="utf-8") as source:
                report = summarize(source, args.request_id)
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"Could not read log input: {error}\n")
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
