# Интеграции (Telegram, Google)

Telegram
- Отправка сообщений: ferum_custom/ferum_custom/ferum_custom/integrations/telegram.py
- Настройки: `Ferum Custom Settings` → `telegram_bot_token`, `telegram_default_chat_id`.

Google Drive
- Загрузка PDF табелей учета рабочего времени: ferum_custom/ferum_custom/ferum_custom/integrations/drive.py
- Требуется сервисный аккаунт (JSON) и корневая папка: `google_service_account_json`, `google_drive_root_folder_id`.

Google Sheets
- Синхронизация счетов: ferum_custom/ferum_custom/ferum_custom/doctype/invoice/invoice.py
- Настройки/флаг: `enable_google_sheets_sync`, `google_service_account_json`, `google_sheet_name`.

Общие хелперы Google
- Построение Credentials из JSON во вложении: ferum_custom/ferum_custom/ferum_custom/integrations/google.py
