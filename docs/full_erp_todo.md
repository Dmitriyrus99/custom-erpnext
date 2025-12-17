# Full ERP Migration TODO (Ferum Custom)

## Phase 1 — Быстрые выигрыши

- [x] SR: добавить поле `sla_policy` (Link→SLA Policy), обновить расчет SLA, кэшировать customer/project/department из Service Object/Project.
- [x] Индексы: `Service Request` (company,status),(service_object),(assigned_to),(sla_deadline); `Service Report` (service_request),(company,report_date); `Invoice` (company,service_project),(sales_invoice); `Payment Allocation` (invoice),(payment).
- [x] Автозаполнение SR: если задан service_object → заполнить customer/project/department/company + assigned_to (object default, иначе project default).
- [ ] Рефреш билда и кэшей включить в deploy-пайплайн (bench build --force + restart).

## Phase 2 — Структурные изменения

- [ ] Контрагент: добавить ссылку `customer` в `Counterparty`, мигрировать ссылки в Payment/Contract/Projects на `Customer`; определить путь отказа от дублирования. _(в работе: Invoice/Payment/Contract уже требуют Customer, миграция Counterparty→Customer выполнена частично)_
- [ ] Упростить SR схему: хранить customer/project/department как cached, но источник — объект/проект; избавиться от `linked_report` в пользу 1:N Service Report → SR.
- [ ] Финансы: в `Invoice` добавить `service_request` (или `service_report`), `item_code` (опц.), автоподстановка `cost_center`/`income_account` из Settings; recalculation hook.

## Phase 3 — Полноценный ERP

- [ ] Перейти на стандартные `Sales Invoice`/`Payment Entry`, отказаться от кастом `Invoice`/`Payment Allocation`.
- [ ] Ввести `Item` для услуг/материалов; при необходимости `Delivery Note`/`Stock Entry`.
- [ ] Депрецировать `Project` в пользу `Service Project`; вычистить SLA-дубли в `Issue`.
- [ ] Оптимизировать планировщики: батчи для Maintenance Schedule, SLA monitor, материализованные отчеты.

### Формат выполнения

- Каждая задача фиксируется коммитом/патчем + миграцией (при изменении схемы).
- Минимизировать кастомный код, отдавая приоритет стандартным механизмам ERPNext.
