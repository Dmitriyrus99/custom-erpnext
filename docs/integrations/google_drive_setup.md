# Google Drive Integration Setup

This guide walks through configuring the Ferum Custom Google Drive integration on ERPNext v15 (service-account flow). The integration mirrors attachments, service reports, and scheduled backups to Drive and is guard-railed by the `enable_google_drive_sync` feature flag.

## Prerequisites

- Google Cloud project with the Drive API enabled.
- Service Account with access to the destination Drive folder(s).
- ERPNext site with the Ferum Custom app installed.
- Bench shell with access to upload files / edit single doctypes.

## 1. Create service account credentials

1. Open [Google Cloud Console → IAM & Admin → Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Create a new service account (or reuse an existing one dedicated to document storage).
3. Grant the **Drive API** role `Project → Editor` or a custom role with at least `drive.file`/`spreadsheets`.
4. Under “Keys” generate a **JSON key**, download it, and upload it straight to Vault/SSM (or at least into ERPNext as a private File). Do not commit the JSON to git.

> :lock: Rotate keys periodically; track versioned secrets (e.g., `FERUM_GOOGLE_SERVICE_ACCOUNT_JSON_V2`) and switch over via `scripts/render_env.py`.

## 2. Prepare Google Drive

1. Decide on a root folder (e.g. _Ferum Archive_). Copy its folder ID (the 33-character string in the URL).
2. Share the folder with the service account email (e.g. `ferum-drive@project.iam.gserviceaccount.com`) with at least **Editor** access (can be limited to a shared drive).

Ferum will create sub-folders automatically:

- `/Customer/<Project>/Reports` for service report PDFs.
- `/Customer/<Project>/Attachments` for attachments.
- `/<site>/Backups/` for SQL backups (if enabled).

## 3. Upload the service account JSON to ERPNext

1. Open the Desk → “Files” and upload the JSON file as a **private** File.
2. Note the resulting File URL (e.g. `/private/files/ferum-drive.json`). No repository changes are required.

## 4. Configure Ferum Custom Settings

1. Desk → “Ferum Custom Settings”.
2. Under **Integrations**:
   - Ensure **Enable Google Drive Sync** is checked.
   - Set **Google Service Account JSON** to the uploaded file.
   - Set **Drive Root Folder ID** to the folder ID from step 2.
3. Save the document.

### Environment overrides (optional)

You can override settings per environment without desk access via environment variables:

```bash
export FERUM_ENABLE_GOOGLE_DRIVE_SYNC=1
export FERUM_GOOGLE_DRIVE_ROOT_FOLDER_ID=1abCDefGhIJkLmNoPQrStUvWxYZ
```

Variables follow the pattern `FERUM_<fieldname in uppercase>`. See `config/.env.example.integrations` for a template.

## 5. Validate the integration

1. Use the **Check Google Drive** button on “Ferum Custom Settings”. The new healthcheck:
   - Reads the root folder metadata (`files().get`) and reports owner/link.
   - Verifies write access by creating a tiny `healthcheck-<timestamp>.txt`, checking it exists, then deleting it.
   - Returns structured JSON so Prometheus/Grafana can parse `status`/`message`.
   - Mirror the same checks via `/api/method/ferum_custom.api.drive.health`, which reads credentials from `.env` and can be polled by Prometheus/CI without logging into ERPNext.
2. Trigger a manual sync:
   - Submit a “Service Report” and confirm the PDF appears under `/Customer/<Project>/Reports`.
   - Attach a file to a Service Request; verify both `Custom Attachment` and the File link contain `drive_file_id`.
3. CLI smoke test:

```bash
bench --site <site> execute ferum_custom.ferum_custom.site_ops.backup_to_drive
```

Check the Drive folder for a `.sql.gz` backup (deleted by background cleanup after verification).

## 6. Monitoring & troubleshooting

- Upload failures log errors and email **System Manager** + **Chief Accountant**.
- Healthcheck output feeds Prometheus/Grafana; alert when `status` != `ok`.
- Retry: 3× on HTTP 429/5xx with exponential backoff; see `drive.upload_bytes`.
- Disable `FERUM_ENABLE_GOOGLE_DRIVE_SYNC` if the service account temporarily loses access.

## 7. DocType/process dependencies

- `Service Report` → PDF export and upload under `/Customer/<Project>/Reports`.
- `Service Request` files → stored as `Custom Attachment`, `File`, and optionally synced to Drive if `enable_google_drive_sync`.
- `Invoice` data (via `sync_to_google_sheets`) → writes rows to the configured sheet.
- `Service Maintenance Schedule` backups → archived under `<site>/Backups/`.

Drive integration only works after the service account JSON and root folder id propagate into `.env` via your Secret Manager (vault/SSM) + `scripts/render_env.py`. The runtime now favors these environment overrides for sensitive fields (`FERUM_GOOGLE_SERVICE_ACCOUNT_JSON`, etc.), so keep them out of Desk settings and supply them via Vault/SSM every deploy.

## 7. Security checklist

- Keep service-account JSON outside version control; upload via Desk only.
- Use least-privilege scopes. The integration currently requests full Drive scope; consider restricting the service account to a dedicated shared drive.
- Rotate secrets when staff changes or devices are compromised.
- Monitor Drive audit logs for unusual access (e.g., downloads outside business hours).

## 8. Common issues

| Symptom                                                   | Resolution                                                                                                                 |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Healthcheck → `google-api-python-client is not installed` | `pip install google-api-python-client` in the bench environment and restart workers.                                       |
| Upload returns `HTTP 403`                                 | Service account lacks permission on folder; re-share the folder or check shared drive settings.                            |
| Files stuck locally (`drive_file_id` empty)               | Ensure feature flag is enabled and the background worker queue `short` is running.                                         |
| Backups missing                                           | Run the `backup_to_drive` command manually to obtain stack trace, verify bench user has read permissions to backup folder. |

With these steps complete the Drive integration is production-ready, auditable, and easy to verify through the new healthcheck button.
