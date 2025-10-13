# Changelog

## [Unreleased]

### Added
- Service Report: strict attachment validation on validate (require at least one image and one PDF act) and automatic linking of `Custom Attachment` to the report for Drive sync.
- Data patch `v15_1.sync_service_report_attachment_links` to backfill attachment links for existing Service Reports (idempotent).
- Audit comment on Service Request when a Service Report is submitted and linked.
- Telegram: generic JWT-protected upload endpoints for attaching files to Service Request/Service Report.
- Telegram: Aiogram 3 bot scaffold with handlers, inline buttons, Frappe API client, Docker/systemd configs.
- Patch `v15_1.bootstrap_telegram_settings` to seed Telegram settings defaults (idempotent).
- Telegram: `Telegram User Link` DocType for mapping ERPNext users to Telegram chat IDs and admin flag; webhook now impersonates mapped user.

### Improved
- Google Drive consistency by ensuring all attachments referenced by Service Report are linked and synchronized under `/Customer/Project/Reports`.
 - Telegram webhook hardened with official secret header verification.
