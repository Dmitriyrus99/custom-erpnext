#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT_DIR/.fastmcp-venv"
PYTHON_BIN="${PYTHON_BIN:-python3.12}"
REQUIRED_VERSION="2.14.1"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "[fastmcp] '$PYTHON_BIN' not found. Set PYTHON_BIN=python3.12 (or install Python 3.12)." >&2
  exit 1
fi

if [[ ! -d "$VENV" ]]; then
  echo "[fastmcp] Creating venv: $VENV"
  "$PYTHON_BIN" -m venv "$VENV"
fi

echo "[fastmcp] Installing fastmcp==$REQUIRED_VERSION"
"$VENV/bin/pip" install --upgrade pip
"$VENV/bin/pip" install "fastmcp==$REQUIRED_VERSION"

echo "[fastmcp] Done. Run: ./scripts/run_fastmcp.sh"

