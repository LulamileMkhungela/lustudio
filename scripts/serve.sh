#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../cosmos-copy"
exec python3 -m http.server "${1:-3000}" --bind 0.0.0.0
