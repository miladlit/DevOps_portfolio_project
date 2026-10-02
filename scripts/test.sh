#!/usr/bin/env bash
# Resolve the repository from this script, regardless of the current directory.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
python3 -m unittest discover -s tests -v
