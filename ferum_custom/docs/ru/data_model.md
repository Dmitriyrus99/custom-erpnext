# Модель данных (DocTypes)

- Проекты: Project — связь с Клиентом, Активами, Заявками и Счетами.
- Заявки: Issue — SLA, статусы, назначение инженера, связь с табелем учета рабочего времени.
- Табели учета рабочего времени: Timesheet — работы, документы, PDF, выгрузка в Drive.
- Счета: Invoice — статусы, синхронизация с Google Sheets, опциональное создание ERPNext Sales Invoice.

Файлы и связи:
- ER: ../entity_relationship_model.md
- Project: ferum_custom/ferum_custom/ferum_custom/doctype/project/
- Issue: ferum_custom/ferum_custom/ferum_custom/doctype/issue/
- Timesheet: ferum_custom/ferum_custom/ferum_custom/doctype/timesheet/
- Invoice: ferum_custom/ferum_custom/ferum_custom/doctype/invoice/
