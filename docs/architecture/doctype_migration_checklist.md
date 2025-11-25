# DocType Migration Checklist

Этот чек-лист фиксирует, как каждая кастомная сущность должна выглядеть после миграций (поля, уникальные ключи, child tables, индексы и legacy-артефакты). Он базируется на `architecture_overview.md` и используется в Stage 3 для написания патчей.

| DocType | Key fields / description | Unique keys / indexes | Child tables / dependencies | Legacy cleanup / notes |
| --- | --- | --- | --- | --- |
| `Counterparty` | `name`, `company`, `counterparty_type`, `name_short`, `inn`, `kpp`, `address` (link) | `(company, counterparty_type, name_short)`, `(company, inn)` | `Counterparty Contact` | Remove old vendor/customer tables that duplicate this model |
| `Project` | `name`, `company`, `code`, `customer` (Counterparty), `service_department` | `(company, code)` | Parent for `Service Object`, `Contract`, `Service Request` | Drop obsolete project-like tables from legacy schema |
| `Contract` / `Contract Stage` | `contract_no`, `contract_year`, `contract_no_normalized`, `customer`, `project`, `date_start`, `date_end`, `amount_max`, `currency` | `(company, contract_year, contract_no)` + normalized index on `contract_no_normalized` | Child `Contract Stage` | Remove legacy Contract tables (v15_mariadb patch references); `normalize_contracts_job` keeps `contract_no_normalized` updated and logs `Data Issue` on duplicates. |
| `Service Object` | `company`, `project`, `customer`, `location`, `serial_no`, `default_engineer` | `(company, object_name)` | Parent for `Service Request`, `Service Report` | Retire old `Service Center` tables |
| `Service Request` / `Service Report` | `company`, `project`, `service_object`, `status`, `linked_report`, `sla_policy` | Index on `(company, status)`, `(service_object)` | `Service Request` → `Service Report`, `Service Report` child work_items/docs | Drop `Issue`/`Timesheet` remnants used before ERPNext migration; `cleanup_legacy_service_request_tables` patch removes the old Legacy tables the scheduler platforms no longer use. |
| `Invoice` / `Invoice Item` | `company`, `invoice_no`, `invoice_year`, `counterparty`, `status`, `amount`, `sales_invoice` | `(company, invoice_year, invoice_no)` + normalized field | Child `Invoice Item` | Remove custom tables that replicated `Sales Invoice` |
| `Payment` / `Payment Allocation` | `company`, `trx_date`, `direction`, `amount`, `account`, `article`, `counterparty`, `doc_ref` | Index on `company`, `direction` | `Payment Allocation` (links invoice/payment) | Remove legacy payment tables/triggers |
| `Service Maintenance Schedule` | `company`, `customer`, `service_project`, `Periodicity` | `(service_project, schedule_name)` | Generates `Service Request` via scheduler | Clean up outdated scheduling tables |
| `Data Issue` | `entity`, `entity_id`, `severity`, `message`, `detected_at`, `resolved_at` | Index on `(entity, severity, resolved_at)` | Used by ETL and audit jobs | Ensure duplicates logged only once |
| `Stg Raw` | `company`, `source_file`, `sheet`, `row_json`, `ingested_at` | `(company, source_file, sheet)` | Feeds ETL pipelines | Daily `cleanup_stg_raw_job` prunes rows older than the retention window and `add_unique_indexes` ensures an `ingested_at` index to keep truncations fast. |
| `Cashflow Article` | `name`, `direction`, `group_name` | `(direction, group_name)` | Linked from `Payment` | Remove legacy article tracking tables |

Дополните таблицу по мере уточнения полей или обнаружения новых зависимостей.

## Migration patches & jobs

- `ferum_custom.patches.v15_4.normalize_contracts` / `data_cleanup.jobs.normalize_contracts_job` populates `contract_no_normalized` and logs duplicates as `Data Issue`.
- `ferum_custom.patches.v15_4.add_unique_indexes` enforces indexes on `Contract`, `Invoice`, `Payment`, and `Stg Raw`, improving migration stability and cleanup speed.
- `ferum_custom.patches.v15_4.cleanup_legacy_service_request_tables` drops the leftover legacy `Service Request`/`Service Report` tables so the schema matches ERPNext.
- `ferum_custom.ferum_custom.data_cleanup.jobs.cleanup_stg_raw_job` runs daily (via the scheduler) to trim `Stg Raw` entries outside the retention window before fresh ETL ingestions.
