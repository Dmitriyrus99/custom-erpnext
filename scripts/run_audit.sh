#!/bin/bash
echo "🚀 Запуск AI-аудита Ferum Customizations..."
codex create-task audit-prod-ready \
  --prompt-file ./scripts/prompts/audit_and_cleanup.txt \
  --path ./ \
  --output ./docs/audit/
