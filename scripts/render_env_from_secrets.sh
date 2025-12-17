#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: render_env_from_secrets.sh --provider <vault|aws-ssm> --path <path> --output <file>

Options:
  --provider   Required. Either "vault" (HashiCorp KV v2) or "aws-ssm" (AWS Parameter Store).
  --path       Required. Secret manager path (e.g. secret/ferum/dev or /ferum/dev).
  --output     Optional. File to write KEY=VALUE pairs to (default stdout).
  --help       Show this message.
EOF
  exit 1
}

PROVIDER=""
SECRET_PATH=""
OUTPUT="/dev/stdout"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider)
      PROVIDER="${2:-}"
      shift 2
      ;;
    --path)
      SECRET_PATH="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --help)
      usage
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "$PROVIDER" || -z "$SECRET_PATH" ]]; then
  echo "Error: --provider and --path are required" >&2
  usage
fi

command_exists() {
  command -v "$1" > /dev/null 2>&1
}

if [[ "$PROVIDER" == "vault" ]]; then
  if ! command_exists vault; then
    echo "vault CLI is required for provider vault" >&2
    exit 1
  fi
  if ! command_exists jq; then
    echo "jq is required to parse Vault output" >&2
    exit 1
  fi
  VAULT_OUTPUT=$(vault kv get -format=json "$SECRET_PATH")
  echo "$VAULT_OUTPUT" | jq -r '.data.data | to_entries[] | "\(.key)=\(.value)"' > "$OUTPUT"
elif [[ "$PROVIDER" == "aws-ssm" ]]; then
  if ! command_exists aws; then
    echo "aws CLI is required for provider aws-ssm" >&2
    exit 1
  fi
  if ! command_exists jq; then
    echo "jq is required to parse AWS CLI output" >&2
    exit 1
  fi
  aws ssm get-parameters-by-path \
    --path "$SECRET_PATH" \
    --with-decryption \
    --recursive \
    --output json \
    | jq -r '.Parameters[] | "\(.Name | split("/") | last)=\(.Value)"' > "$OUTPUT"
else
  echo "Unsupported provider: $PROVIDER" >&2
  exit 1
fi
