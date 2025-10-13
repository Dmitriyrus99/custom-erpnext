# Ferum Telegram Bot (Aiogram 3)

This is a separate bot service using Aiogram 3.x that integrates with Frappe/ERPNext Ferum Customizations.

Features:
- JWT-authenticated calls to Frappe custom API
- Create Service Requests, list own/assigned, change status via inline buttons
- Attach photos/documents to Service Request and Service Report (multipart upload)
- Optional Sentry error reporting and Prometheus metrics
- Webhook or polling mode (recommended: webhook behind Traefik HTTPS)

See `../../ferum_custom/docs/telegram_integration.md` for deployment.
