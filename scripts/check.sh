#!/usr/bin/env bash
# Check the HTTP response and its JSON payload; fail on either kind of error.
set -euo pipefail
if (( $# > 1 )); then
  echo "Usage: bash scripts/check.sh [base-url]" >&2
  exit 2
fi
service_url="${1:-http://127.0.0.1:8000}"
curl --fail --silent --show-error --max-time 5 "${service_url%/}/health" |
  python3 -c '
import json
import sys
try:
    if json.load(sys.stdin) != {"status": "ok"}:
        raise ValueError("unexpected health payload")
except (ValueError, OSError) as error:
    print(f"Health check failed: {error}", file=sys.stderr)
    sys.exit(1)
print("Health check passed")
'
