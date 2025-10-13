# Автоматизация при подтверждении Service Report

Цель: обеспечить автоматическое обновление связанной заявки, проверку обязательных вложений и синхронизацию файлов в Google Drive при подтверждении (Submit) документа Service Report.

## Бизнес-логика

- При `Submit` Service Report:
  - В связанной `Service Request` заполняется поле `linked_report` и статус переводится в `Completed`.
  - Создаётся PDF «ServiceReport-{name}.pdf», который прикрепляется к Service Report как `File` и регистрируется как `Custom Attachment`.
  - Запускается фоновая загрузка PDF и вложений в Google Drive в структуру папок `/Customer/Project/Reports`.
  - В Service Request добавляется комментарий «Linked Service Report {SRPT-...}» (аудит).

- Валидация вложений (на этапе `validate` Service Report):
  - В таблице `documents` должен быть хотя бы один элемент.
  - Должна присутствовать хотя бы одна фотография (MIME `image/*`).
  - Должен присутствовать хотя бы один файл акта/отчёта в формате PDF (MIME `application/pdf`).
  - Любой указанный `Custom Attachment` автоматически помечается ссылкой на текущий Service Report (`linked_doctype = "Service Report"`, `linked_docname = SRPT-...`) для корректной синхронизации с Drive.

Примечание: PDF, генерируемый системой при `Submit`, удовлетворяет требованию «акт (PDF)». Если требуется именно подписанный скан акта, добавьте его отдельным вложением — валидация все равно проверит наличие PDF.

## Техническая реализация

- Файл: `ferum_custom/doctype/service_report/service_report.py`
  - Методы:
    - `validate_attachments()` — расширен: проверяет наличие фото и PDF; использует MIME из `Custom Attachment.file_type` либо вычисляет по имени.
    - `_sync_document_links_to_attachments()` — гарантирует, что все `Custom Attachment` из `documents` ссылаются на текущий Service Report для Drive-синхронизации.
    - `on_submit()` — не изменялся по контракту, вызывает обновление заявки и генерацию/загрузку PDF.
    - `update_service_request_on_submit()` — дополняет аудит-комментарием в заявке.

- Патч: `patches/v15_1/sync_service_report_attachment_links.py`
  - Идемпотентный бэкфилл ссылок `linked_doctype/docname` для вложений в уже существующих Service Report.
  - Добавлен в `patches.txt` в секцию `[post_model_sync]`.

## Тест-кейсы (ручные или автотесты)

1) Submit с корректными вложениями
   - Создать Service Report с `documents`: одно фото (jpg/png) и один PDF.
   - Submit → статус Service Request = `Completed`, поле `linked_report` = имя Service Report.
   - В Service Request добавлен комментарий о связке.
   - В Service Report есть `File` и `Custom Attachment` с PDF; файлы получают `linked_doctype/docname` = текущий Service Report.

2) Отсутствует фото
   - Удалить все изображения из `documents`.
   - Сохранение/Submit → ошибка: «At least one photo (image) attachment is required.»

3) Отсутствует PDF
   - Оставить только изображения в `documents`.
   - Сохранение/Submit → ошибка: «An Act (PDF) attachment is required.»

4) Бэкфилл ссылок
   - На существующих Service Report документы указывают на `Custom Attachment` без `linked_doctype/docname`.
   - Запустить миграции (или bench migrate) → патч проставит связи корректно.

5) Drive синхронизация
   - Включить флаг `enable_google_drive_sync`.
   - Submit Service Report → файлы попадают в папки `/Customer/Project/Reports`.

## Безопасность и доступ

- Доступ ограничивается через Permission Query Conditions и `has_permission` логикой Service Report/Service Request.
- Все API защищены JWT-мидлварой (`hooks.before_request`).
- Действия логируются через комментарии/сообщения и стандартный аудит Frappe.

