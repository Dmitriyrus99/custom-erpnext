#!/usr/bin/env bash
set -euo pipefail
SITE="${1:-site.local}"
bench --site "$SITE" migrate
echo "OK"
