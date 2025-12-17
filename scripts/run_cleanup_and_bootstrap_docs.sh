#!/usr/bin/env bash
set -euo pipefail

PROJECT="/home/frappe/frappe-bench/frappe-bench"
cd "$PROJECT"

echo "▶ Project: $PROJECT"

# --- helpers ---
ensure_dir() { mkdir -p "$1"; }
move_if_exists() { local f="$1"; local dest="$2"; if [ -e "$f" ]; then ensure_dir "$dest"; echo "  → move $f -> $dest/"; git mv -f "$f" "$dest/" 2>/dev/null || mv -f "$f" "$dest/"; fi; }
rm_from_git_if_exists() { local f="$1"; if git ls-files --error-unmatch "$f" >/dev/null 2>&1; then echo "  ✖ remove from git: $f"; git rm -f --cached "$f" || true; fi; if [ -e "$f" ]; then rm -f "$f"; fi; }
append_once() { local file="$1"; local line="$2"; grep -qxF "$line" "$file" 2>/dev/null || echo "$line" >> "$file"; }

# --- 0. sanity ---
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "❌ Не git-репозиторий: $PROJECT"; exit 1
fi

# --- 1. legacy bucket ---
LEGACY_DIR="$PROJECT/legacy"
ensure_dir "$LEGACY_DIR"

echo "▶ Перемещение LEGACY файлов..."
# корень
move_if_exists "install_frappe.log" "$LEGACY_DIR"
move_if_exists "install_erpnext.log" "$LEGACY_DIR"
move_if_exists "install_erpnext_force.log" "$LEGACY_DIR"
move_if_exists "install_erpnext_attempt.log" "$LEGACY_DIR"
move_if_exists "updated_doctypes_json.zip" "$LEGACY_DIR"
move_if_exists "REBUILD_PROGRESS.md" "$LEGACY_DIR"
move_if_exists "audit_report.md" "$LEGACY_DIR"
move_if_exists "REBUILD_PLAN.md" "$LEGACY_DIR"
move_if_exists "SYSTEM_FIX_AUDIT.md" "$LEGACY_DIR"
move_if_exists "data_model_rebuild.md" "$LEGACY_DIR"
move_if_exists "cleanup_candidates.md" "$LEGACY_DIR"
move_if_exists "architecture_updated.drawio" "$LEGACY_DIR"
# BPMN переносим в legacy только если появится новая схема — пока оставим на месте.

# changes/
move_if_exists "changes/quick_fixes.md" "$LEGACY_DIR/changes"
move_if_exists "changes/telegram_integration_audit.md" "$LEGACY_DIR/changes"  # будет слито в docs/integrations/telegram.md вручную/на этапе 2

# scripts/prompts
move_if_exists "scripts/prompts/audit_and_cleanup.txt" "$LEGACY_DIR/scripts_prompts"

# --- 2. remove (секреты, рантайм, мусор) ---
echo "▶ Удаление секретов/рантайма из репо и .git..."
rm_from_git_if_exists "config/.env.integrations"
rm_from_git_if_exists "config/redis_queue.acl"
rm_from_git_if_exists "config/redis_cache.acl"
rm_from_git_if_exists "config/pids/temp-25696.rdb"
rm_from_git_if_exists "config/pids/redis_queue.rdb"
rm_from_git_if_exists "config/test_global.lock"
rm_from_git_if_exists "config/site_config.lock"
rm_from_git_if_exists "config/monitor_flush.lock"
rm_from_git_if_exists "config/bench_build.lock"

# --- 3. .gitignore hardening ---
echo "▶ Обновление .gitignore..."
touch .gitignore
append_once .gitignore ".env"
append_once .gitignore "*.acl"
append_once .gitignore "*.rdb"
append_once .gitignore "*.lock"
append_once .gitignore "*.log"
append_once .gitignore "/legacy/"
append_once .gitignore "/sites/*/private/backups/"
append_once .gitignore "node_modules/"
append_once .gitignore "dist/"
append_once .gitignore "assets/"
append_once .gitignore ".bench/"
append_once .gitignore ".DS_Store"

# --- 4. scaffold docs ---
echo "▶ Создание каркаса новой документации..."
ensure_dir "docs/audit"
ensure_dir "docs/architecture"
ensure_dir "docs/integrations"

create_if_absent() {
  local path="$1"; shift
  if [ ! -e "$path" ]; then
    printf "%s\n" "$@" > "$path"
    echo "  + $path"
  else
    echo "  = $path (существует)"
  fi
}

create_if_absent "docs/index.md" \
"# Документация проекта (каркас)
- [Аудит](./audit/current_audit.md)
- [Архитектура](./architecture/architecture_overview.md)
- [План поставки](./delivery_plan.md)
- [Инфраструктура и CI/CD](./infrastructure_and_ci.md)
- [Роли и ACL](./roles_and_acl.md)
- [Заметки по легаси](./legacy_notes.md)
"

create_if_absent "docs/audit/current_audit.md" \
"# Текущий аудит (каркас)
> TODO: консолидировать выводы из предыдущих аудитов (перенесены в /legacy) и из audit_inventory.md.
"

create_if_absent "docs/architecture/architecture_overview.md" \
"# Обзор архитектуры (каркас)
## Контуры: web / workers / scheduler / socketio
## Хранилища: MariaDB|Postgres, Redis (cache/queue/socketio), внешние (Drive)
## Интеграции: Telegram, Google Drive/Sheets, Prometheus/Sentry
## ACL и роли: Admin, Manager, Engineer, Office, Client
## Автоматизация: hooks, cron, site_ops, webhooks
> TODO: заполнить на Этапе 2.
"

# drawio-заглушка как маркер (пустой файл)
touch "docs/architecture/current_diagram.drawio"

create_if_absent "docs/delivery_plan.md" \
"# Delivery Plan (каркас)
> TODO: слить REBUILD_PLAN.md, improvement_plan.csv и релевантное из REBUILD_PROGRESS.md (все в /legacy) в единый план с приоритетами P0/P1/P2.
"

create_if_absent "docs/infrastructure_and_ci.md" \
"# Инфраструктура и CI/CD (каркас)
## Envs: dev/stage/prod
## IaC: Terraform + Ansible/bench
## CI: lint → pytest → bench migrate (dry-run) → build → deploy → notify
## Мониторинг: Prometheus/Grafana, Sentry
## Секреты: Vault/SSM, примеры .env.*.example
## DR/Backups: расписание, шифрование, test-restore
"

create_if_absent "docs/roles_and_acl.md" \
"# Роли и ACL (каркас)
> TODO: объединить user_role_instructions.md и user_role_instructions_detailed.md в единый документ и удалить дубли.
"

create_if_absent "docs/legacy_notes.md" \
"# Legacy Notes (каркас)
> Здесь краткие выдержки из перенесённых в /legacy документов. Не использовать как источник истины.
"

# --- 5. Обновить README.md на минимальный индекс на новые docs ---
echo "▶ Обновление README.md..."
cat > README.md <<'MD'
# Ferum / ERPNext — Репозиторий

Актуальная документация:
- **Аудит:** `docs/audit/current_audit.md`
- **Архитектура:** `docs/architecture/architecture_overview.md`
- **План поставки:** `docs/delivery_plan.md`
- **Инфраструктура и CI/CD:** `docs/infrastructure_and_ci.md`
- **Роли и ACL:** `docs/roles_and_acl.md`
- **Legacy заметки:** `docs/legacy_notes.md`

> Прежние документы перенесены в `/legacy/` и не являются источником истины.
MD

# --- 6. Коммит ---
echo "▶ git add & commit..."
git add -A
git commit -m "chore(repo): move legacy docs, remove secrets/runtime from VCS, bootstrap new docs scaffold, harden .gitignore"

echo "✅ Готово. Проверь diff и push."
