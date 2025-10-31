#!/usr/bin/env bash
# Ubuntu 24.04.3 LTS — создание и установка кастомного приложения Frappe/ERPNext

set -Eeuo pipefail

# ---------- 1) ПАРАМЕТРЫ ----------
APP_NAME="ferum_custom"

APP_TITLE="Ferum Custom"
APP_DESCRIPTION="Custom erp system for Ferum"
APP_PUBLISHER="Ferum"
APP_EMAIL="rusakov@ferumrus.ru"
APP_LICENSE="MIT"
APP_VERSION="0.0.1"

FRAPPE_BENCH_PATH="/home/frappe/frappe-bench/frappe-bench"
SITE_NAME="erp.ferumrus.ru"

GIT_REPO_URL="https://github.com/Dmitriyrus99/custom-erpnext.git"
GIT_DEFAULT_BRANCH="main"

# ---------- 2) ХЕЛПЕРЫ ----------
die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo -e ">>> $*"; }

# Рекомендуется выполнять под пользователем frappe (не root)
if [ "$(id -u)" -eq 0 ]; then
  echo "⚠️ Рекомендуется запускать скрипт от пользователя 'frappe', не от root."
fi

# Локали, чтобы избежать проблем с кодировкой
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

# Добавим ~/.local/bin в PATH (часто там лежит bench)
export PATH="$HOME/.local/bin:$PATH"

# ---------- 3) ПРОВЕРКИ ОКРУЖЕНИЯ ----------
[ -d "$FRAPPE_BENCH_PATH" ] || die "Директория bench не найдена: $FRAPPE_BENCH_PATH"

command -v bench >/dev/null 2>&1 || die "Команда 'bench' не найдена в PATH. Проверьте установку (pipx/pip --user) и PATH."

# Проверим, что в бенче есть typical файлы/структура
[ -f "$FRAPPE_BENCH_PATH/Procfile" ] || info "Предупреждение: в $FRAPPE_BENCH_PATH не найден Procfile (проверка пропущена)."

cd "$FRAPPE_BENCH_PATH"

# Проверим существование сайта
if ! bench list-sites | awk '{print $1}' | grep -Fxq "$SITE_NAME"; then
  die "Сайт '$SITE_NAME' не найден в текущем bench. Создайте сайт или исправьте SITE_NAME."
fi

# ---------- 4) СОЗДАНИЕ ПРИЛОЖЕНИЯ (ИДЕМПОТЕНТНО) ----------
if [ -d "apps/$APP_NAME" ]; then
  info "Приложение '$APP_NAME' уже существует в apps/. Пропускаю bench new-app."
else
  info "Создаю новое приложение: $APP_NAME"
  bench new-app "$APP_NAME" \
    --app_title="$APP_TITLE" \
    --app_description="$APP_DESCRIPTION" \
    --app_publisher="$APP_PUBLISHER" \
    --app_email="$APP_EMAIL" \
    --app_license="$APP_LICENSE" \
    --app_version="$APP_VERSION"
fi

# ---------- 5) УСТАНОВКА ПРИЛОЖЕНИЯ НА САЙТ ----------
# Проверим, не установлено ли уже
if bench --site "$SITE_NAME" list-apps | grep -Fxq "$APP_NAME"; then
  info "Приложение '$APP_NAME' уже установлено на сайт '$SITE_NAME'. Пропускаю install-app."
else
  info "Устанавливаю приложение '$APP_NAME' на сайт '$SITE_NAME'..."
  bench --site "$SITE_NAME" install-app "$APP_NAME"
fi

# ---------- 6) МИГРАЦИИ ----------
info "Запускаю миграции базы данных..."
bench --site "$SITE_NAME" migrate

# ---------- 7) НАСТРОЙКА GIT (ИДЕМПОТЕНТНО) ----------
cd "apps/$APP_NAME"

# Инициализация репозитория, если ещё не инициализирован
if [ ! -d ".git" ]; then
  info "Инициализирую git-репозиторий в apps/$APP_NAME"
  git init
  git add .
  git commit -m "feat: initial commit of the application structure" || true
  git branch -M "$GIT_DEFAULT_BRANCH"
fi

# Настроим origin, если не задан
if ! git remote get-url origin >/dev/null 2>&1; then
  if [ -n "$GIT_REPO_URL" ]; then
    info "Добавляю удалённый репозиторий origin: $GIT_REPO_URL"
    git remote add origin "$GIT_REPO_URL"
    info "Готово. Для загрузки кода выполните: git push -u origin $GIT_DEFAULT_BRANCH"
  else
    info "GIT_REPO_URL пуст. Пропускаю настройку origin."
  fi
else
  info "remote 'origin' уже настроен. Пропускаю."
fi

info "✅ Готово! Приложение '$APP_NAME' создано/проверено и установлено на сайт '$SITE_NAME'."
