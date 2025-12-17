# Финансовая миграция

В рамках перехода от кастомных `Invoice` / `Payment Allocation` к стандартным `Sales Invoice` / `Payment Entry` введён механизм поэтапной миграции.

## Флаги фич

- `Ferum Custom Settings.enable_standard_finance` / env `FERUM_ENABLE_STANDARD_FINANCE` — включает создание `Sales Invoice`/`Payment Entry`.
- `Ferum Custom Settings.enable_auto_create_sales_invoice` — при подаче `Invoice` автоматически создаёт `Sales Invoice` (раньше было).

Нормальный порядок:

1. Установить `enable_standard_finance = 1` и (`enable_auto_create_sales_invoice = 1` если нужно).
2. Подать/обновить существующие `Invoice`: в `on_submit` вызывается `ensure_sales_invoice_from_custom`, он создаёт `Sales Invoice` и сохраняет ссылку (`Invoice.sales_invoice`).
3. Существующий `Payment` с `Payment Allocation` автоматически создаёт `Payment Entry` через `ensure_payment_entry_from_custom` при вызове `create_payment_entry_from_payment`.

## На что обратить внимание

- `domain/finance/bridge.py`/`payments.py` — ядро логики, можно вызывать вручную через `bench execute` для отдельных записей для тестов.
- После миграции и полного перевода платежей можно удалить `Payment Allocation`/`Invoice` (или держать как архивные).
- Обновления нужно проверять `ferum_custom/tests/test_finance_flows.py`.

## Проверка и откат

- Отменить флаг `enable_standard_finance` — система возвращается к старому поведению, но новые Sales Invoice/Payment Entry уже созданы.
- Поделать `"Ferum Custom"` документацию/автоматизацию согласно новой схеме (например, scripts/шаблоны).

- Для пакетного прогонки используйте helper helper:
  ```bash
  bench --site <site> execute \\
    ferum_custom.ferum_custom.domain.finance.scripts.migrate_finance.migrate_finance_records \\
    --kwargs '{"limit": 500, "create_sales_invoices": true, "create_payment_entries": true}'
  ```
  Повторяйте до обработки всех старых документов.
