# Google Sheets Integration Setup

This document outlines the setup and configuration for the Google Sheets integration within the Ferum Custom application.

## 1. Prerequisites

- **Google Cloud Project:** A Google Cloud project with the Google Sheets API enabled.
- **Service Account:** A service account with domain-wide delegation enabled if acting on behalf of users, or service account credentials for the application itself.
- **Permissions:** The service account must have at least `Editor` access to the target Google Sheet.

## 2. Configuration in Frappe (`Ferum Custom Settings` DocType)

Navigate to **Setup -> Ferum Custom Settings** in ERPNext.

### Google Drive Settings

- **Enable Google Drive Sync:** (`enable_google_drive_sync`)
  - Set to `true` to enable file synchronization with Google Drive.
- **Google Service Account JSON:** (`google_service_account_json`)
  - Paste the entire content of your Google Service Account JSON key file here. This allows the application to authenticate with Google APIs.
- **Google Drive Root Folder ID:** (`google_drive_root_folder_id`)
  - Specify the ID of the root folder in Google Drive where application files should be stored.

### Google Sheets Settings

- **Enable Google Sheets Sync:** (`enable_google_sheets_sync`)
  - Set to `true` to enable synchronization of invoice data with Google Sheets.
- **Google Sheet Name/ID:** (`google_sheet_name`)
  - Enter the name or ID of the Google Sheet to be used for storing invoice data. If a name is provided, the system will attempt to open the first sheet of the first spreadsheet with that name.

## 3. Monitoring

### Prometheus Metrics

The following metrics are exposed for the Google Sheets integration:

- `ferum_integration_sheets_append_total`:
  - **Description:** Counts the total number of rows appended to Google Sheets.
  - **Labels:** `result` (success/error), `category` (error category if applicable).
- `ferum_integration_sheets_update_total`:
  - **Description:** Counts the total number of rows updated in Google Sheets.
  - **Labels:** `result` (success/error), `category` (error category if applicable).
- `ferum_integration_sheets_read_total`:
  - **Description:** Counts the total number of read operations performed on Google Sheets.
  - **Labels:** `result` (success/error), `category` (error category if applicable).
- `ferum_integration_sheets_health_total`:
  - **Description:** Tracks the health status of the Google Sheets integration.
  - **Labels:** `result` (ok/warning/error), `reason` (e.g., missing_client, no_sheet_id_configured, init_failed, exception).

### Sentry Logging

Errors during Google Sheets operations (connection, upload, read, write) are logged to Sentry using `frappe.log_error` for detailed debugging.

## 4. Health Check

- **Endpoint:** The `healthcheck()` function in `sheets.py` can be called (e.g., via a scheduler job or a custom API endpoint) to verify the integration's status.
- **Check:** It attempts to connect to Google Sheets using configured credentials and read from a test range (`Sheet1!A1`) to confirm permissions and connectivity.
- **Output:** Returns a JSON with `status` (ok/warning/error) and `message`.

## 5. Troubleshooting

- **Authentication Errors (401, 403):** Verify service account credentials, permissions in Google Cloud, and the `google_service_account_json` or `FERUM_GOOGLE_SERVICE_ACCOUNT_JSON_B64` environment variable.
- **Rate Limiting (429):** Implement exponential backoff or reduce the frequency of calls if rate limits are hit.
- **File Not Found / Sheet Not Found:** Ensure the `google_sheet_id` or `google_sheet_name` in Ferum Custom Settings is correct and the service account has access to the specified sheet.
