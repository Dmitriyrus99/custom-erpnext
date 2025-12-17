# FileSync Admin — Diagnostics

The following API methods are available for admins to diagnose Google Drive synchronization and trigger retries.

- Get sync status for a document

  - `GET /api/method/ferum_custom.api.admin_tools.get_file_sync_status?doctype=File&name=<FILE_NAME>`
  - `GET /api/method/ferum_custom.api.admin_tools.get_file_sync_status?doctype=Custom%20Attachment&name=<ATT_NAME>`

  Response:

  - `drive_file_id`, `drive_web_link`, `sync_needed` (boolean)
  - For Custom Attachment: `file_url`, `linked_doctype`, `linked_docname`

- Trigger sync for a document

  - `POST /api/method/ferum_custom.api.admin_tools.trigger_file_sync`
  - Body: `doctype=File|Custom Attachment`, `name=<NAME>`

- List unsynchronized records (minimal admin report)
  - `GET /api/method/ferum_custom.api.admin_tools.list_unsynced_attachments?limit=200`
  - Returns two lists: `attachments[]` (Custom Attachment) and `files[]` (File) without `drive_file_id`.

Tip: Combine with `backfill_drive_ids` scheduler or run it manually for larger batches:

```
bench --site <site> execute ferum_custom.ferum_custom.site_ops.backfill_drive_ids --kwargs '{"limit": 1000}'
```
