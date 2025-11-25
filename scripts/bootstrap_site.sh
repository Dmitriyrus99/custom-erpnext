#!/usr/bin/env bash
set -euo pipefail

# Bootstrap or repair a site with ferum_custom installed.
# Usage: SITE=test_site APP=ferum_custom ./scripts/bootstrap_site.sh

SITE="${SITE:-test_site}"
APP="${APP:-ferum_custom}"

if ! command -v bench >/dev/null 2>&1; then
  echo "bench CLI not found in PATH; activate the bench environment first." >&2
  exit 1
fi

if ! bench --site "$SITE" list-apps >/dev/null 2>&1; then
  echo "Site '$SITE' not found. Create it first: bench new-site $SITE --admin-password <pwd> --mariadb-root-password <pwd>" >&2
  exit 1
fi

if bench --site "$SITE" list-apps | grep -Fxq "$APP"; then
  echo "App '$APP' already installed on site '$SITE'; running migrate + cache clear."
else
  echo "Installing app '$APP' on site '$SITE'..."
  bench --site "$SITE" install-app "$APP"
fi

bench --site "$SITE" migrate
bench --site "$SITE" clear-cache
bench --site "$SITE" clear-website-cache
echo "Site '$SITE' is ready with '$APP'."
