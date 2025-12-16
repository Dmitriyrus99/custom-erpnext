#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT_DIR/.fastmcp-venv"
BIN="$VENV/bin/fastmcp"
CONFIG="$ROOT_DIR/fastmcp.json"
REQUIRED_VERSION="2.14.1"

if [[ ! -d "$VENV" ]]; then
  echo "[fastmcp] Missing venv at $VENV. Create it manually and install fastmcp $REQUIRED_VERSION." >&2
  exit 1
fi

if [[ ! -x "$BIN" ]]; then
  echo "[fastmcp] Binary not found: $BIN. Install fastmcp $REQUIRED_VERSION into the existing venv." >&2
  exit 1
fi

current_version="$($BIN version 2>/dev/null | awk -F: '/FastMCP version/ {gsub(/^ +| +$/, "", $2); print $2}')"
if [[ -z "$current_version" || "$current_version" != "$REQUIRED_VERSION" ]]; then
  echo "[fastmcp] Expected fastmcp $REQUIRED_VERSION, but found '${current_version:-unknown}'. Please reinstall the exact version in $VENV." >&2
  exit 1
fi

# fastmcp run accepts the config file as positional server-spec; no --config-path flag
exec "$BIN" run --skip-env --transport stdio --no-banner --project "$ROOT_DIR" "$CONFIG" "$@"
