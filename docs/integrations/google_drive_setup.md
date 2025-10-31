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
3. Grant the **Drive API** role `Project → Editor` or a custom role with at least `drive.file`.
4. Under “Keys” generate a **JSON key** and download it securely. Keep this file outside of the repository.

> :lock: Rotate keys periodically. Revoke unused keys to minimise exposure.

## 2. Prepare Google Drive

1. Decide on a root folder (e.g. *Ferum Archive*). Copy its folder ID (the 33-character string in the URL).
2. Share the folder with the service account email (e.g. `ferum-drive@project.iam.gserviceaccount.com`) with **Editor** access.

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

1. Open “Ferum Custom Settings” and click **Check Google Drive**.
   - Success shows the folder name and owner.
   - Failure displays the HTTP error code and guidance.
2. Trigger a manual upload:
   - Create or edit a “Service Report” and submit; a PDF should appear under the Drive folder.
   - Attach a file to a Service Request and verify `drive_file_id` is populated on the File record.
3. Optional CLI smoke test:

```bash
bench --site <site> execute ferum_custom.ferum_custom.site_ops.backup_to_drive
```

Check the Drive folder for a new backup `.sql.gz`.

## 6. Monitoring & troubleshooting

- Upload failures create `frappe.log_error` entries and send email to **System Manager** and **Chief Accountant** roles.
- The feature flag can be disabled temporarily to halt uploads without touching code.
- Healthcheck output (button) lists the folder, owner, and link. Use it for on-call playbooks.
- Retry policy: Drive uploads retry 3× on transient HTTP 429/5xx responses with exponential backoff.

## 7. Security checklist

- Keep service-account JSON outside version control; upload via Desk only.
- Use least-privilege scopes. The integration currently requests full Drive scope; consider restricting the service account to a dedicated shared drive.
- Rotate secrets when staff changes or devices are compromised.
- Monitor Drive audit logs for unusual access (e.g., downloads outside business hours).

## 8. Common issues

| Symptom | Resolution |
| --- | --- |
| Healthcheck → `google-api-python-client is not installed` | `pip install google-api-python-client` in the bench environment and restart workers. |
| Upload returns `HTTP 403` | Service account lacks permission on folder; re-share the folder or check shared drive settings. |
| Files stuck locally (`drive_file_id` empty) | Ensure feature flag is enabled and the background worker queue `short` is running. |
| Backups missing | Run the `backup_to_drive` command manually to obtain stack trace, verify bench user has read permissions to backup folder. |

With these steps complete the Drive integration is production-ready, auditable, and easy to verify through the new healthcheck button.
