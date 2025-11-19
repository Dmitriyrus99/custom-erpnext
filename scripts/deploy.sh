#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/docker-compose.production.yml"
ENV_FILE="$REPO_ROOT/.env"
STATE_FILE="$REPO_ROOT/.deploy_state"
CURRENT_IMAGE=""
PREVIOUS_IMAGE=""
ROLLBACK_BACKUP=""

load_env_file() {
  if [ -f "$ENV_FILE" ]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
  fi
}

load_state_file() {
  if [ -f "$STATE_FILE" ]; then
    # shellcheck disable=SC1090
    source "$STATE_FILE"
  fi
}

write_state_file() {
  local current_image="$1"
  local previous_image="$2"
  local backup="$3"

  {
    echo "CURRENT_IMAGE=${current_image:-}"
    echo "PREVIOUS_IMAGE=${previous_image:-}"
    echo "ROLLBACK_BACKUP=${backup:-}"
  } > "$STATE_FILE"
}

run_compose_for_image() {
  local image="$1"
  shift
  ERPNEXT_IMAGE="$image" docker compose -f "$COMPOSE_FILE" "$@"
}

restore_database() {
  local backup_file="$1"

  if [ ! -f "$backup_file" ]; then
    echo "❌ backup not found: $backup_file"
    return 1
  fi

  load_env_file

  echo "🔁 Restoring ${backup_file} into PostgreSQL"
  if [[ "$backup_file" == *.sql ]]; then
    docker compose -f "$COMPOSE_FILE" exec -T postgres \
      psql -U "${POSTGRES_USER:-frappe}" -d "${POSTGRES_DB:-erpnext}" < "$backup_file"
  else
    docker compose -f "$COMPOSE_FILE" exec -T postgres \
      pg_restore -U "${POSTGRES_USER:-frappe}" -d "${POSTGRES_DB:-erpnext}" --clean --if-exists "$backup_file"
  fi
}

deploy() {
  local image="$1"
  if [ -z "$image" ]; then
    echo "❌ deploy command requires an image tag"
    exit 1
  fi

  echo "⬆️ Deploying image $image"
  run_compose_for_image "$image" pull backend worker scheduler
  run_compose_for_image "$image" up -d --no-deps backend worker scheduler
  write_state_file "$image" "${CURRENT_IMAGE:-}" "${BACKUP_FILE:-${ROLLBACK_BACKUP:-}}"

  echo "✅ Deployment finished with image $image"
}

rollback() {
  local target_image="${1:-${PREVIOUS_IMAGE:-}}"
  local backup_file="${2:-${ROLLBACK_BACKUP:-backups/latest.dump}}"

  if [ -z "$target_image" ]; then
    echo "❌ rollback needs a target image (or specify it as the previous image in the state file)"
    exit 1
  fi

  echo "↩️ Rolling back to $target_image"
  run_compose_for_image "$target_image" pull backend worker scheduler
  run_compose_for_image "$target_image" up -d --no-deps backend worker scheduler
  restore_database "$backup_file"
  write_state_file "$target_image" "${CURRENT_IMAGE:-}" "$backup_file"

  echo "✅ Rollback completed to $target_image"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <command> [args]

Commands:
  deploy <image>           pull a docker image and roll the backend/worker/scheduler services forward
  rollback [image] [file]  restore the previous image (fallback to state file) and load a backup
EOF
}

load_state_file

case "${1:-}" in
  deploy)
    deploy "${2:-}"
    ;;
  rollback)
    rollback "${2:-}" "${3:-}"
    ;;
  *)
    usage
    exit 1
    ;;
esac
