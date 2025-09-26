# Архитектура

- Основа: ERPNext (Frappe Framework) + кастом‑приложение `Ferum Custom`.
- Веб‑интерфейсы: внутренний Desk (для менеджеров и инженеров) + портал (простые страницы под роль Client).
- Интеграции и API: модульные интеграции (Telegram, Google Drive/Sheets) внутри приложения; JWT для API.
- Разделение окружений: настройки в `Ferum Custom Settings` (Single DocType) — секреты и флаги по окружениям.

Ссылки:
- Код настроек: ferum_custom/ferum_custom/ferum_custom/settings.py
- Хуки и фикстуры: apps/ferum_custom/ferum_custom/hooks.py
- Обзор: ../system_overview.md
