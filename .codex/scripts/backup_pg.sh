#!/usr/bin/env bash
set -euo pipefail
TS="$(date +%Y%m%d-%H%M%S)"
OUT="backups/pg_${TS}.sql.gz"
mkdir -p backups
pg_dump "${POSTGRES_URL:-postgresql://erp:change_me@localhost:5432/erpnext}" | gzip -9 > "$OUT"
# Ротация: держим 7 дневных
ls -1t backups/pg_*.sql.gz | sed -n '8,$p' | xargs -r rm -f
echo "Backup: $OUT"
