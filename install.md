# Ferum Custom — Install & Setup Guide

This guide helps you configure roles, user permissions, and integrations for a production‑ready setup on Frappe/ERPNext v15.

## Prerequisites

- Running Frappe/ERPNext bench with Site created
- App installed: `bench install-app ferum_custom`

## Roles and Access

- Core roles (fixtures included):
  - Project Manager, Office Manager, Service Engineer, Chief Accountant, Client, Department Head, General Director, System Manager
  - Client is a portal role (no Desk access). Others have Desk access.
- Role Profiles (to simplify assignment):
  - Ferum Admin: System Manager + all Ferum roles (PM, Office, Engineer, Chief Accountant, Director, Dept Head)
  - Ferum Management: General Director, Department Head, Project Manager
  - Ferum Operations: Project Manager, Service Engineer
  - Ferum Accounting: Chief Accountant, Office Manager
  - Ferum Client: Client
  Assign a Role Profile to a user to grant the grouped roles.

### Client access by Customer

Clients see all their Issues, Timesheets and Invoices by Customer, not by owner.

1. Create or select a `Customer` (from Ferum Custom minimal Customer doctype or ERPNext’s Customer if used).
2. Link Client users to their Customer via a `User Permission`:
   - Doctype: `User Permission`
   - User: client’s user
   - Allow: `Customer`
   - For Value: the Customer name

With this in place, portal pages and desk queries will only return records for that Customer.

### Office Manager and Department Head

- Office Manager has full desk access to Issues, Timesheets, Projects and Invoices.
- Department Head has broad access across these doctypes (coarse‑grained until a department field is introduced in the schema).

## Integrations

Open Settings: `Ferum Custom Settings`.

### Google Drive

- Set `Drive Root Folder ID` to the folder under which project and document subfolders are created.
- Custom Attachment uploads and Timesheet PDFs sync to Drive. Errors will also notify System Manager/Chief Accountant.

### Google Sheets (Invoices)

- Enable `Enable Google Sheets Sync`.
- Upload a Service Account JSON (`Google Service Account JSON`).
- Optionally set `Google Sheet Name` (default: Ferum Invoices Tracker).

### Telegram Bot

- Set `Telegram Bot Token` and `Telegram Webhook Secret`.
- Optionally set `Default Chat ID` for broadcast alerts.
- Clients and engineers can use bot commands; sending a photo with caption `/attach ISSUE-NAME` attaches it to the Issue and creates a `Custom Attachment`.

### API & JWT

- Enable `Enable JWT Auth for API` and set `JWT Secret` to allow token‑based access for external portals/integrations.
- Ensure PyJWT is installed in the bench environment (app includes requirements):
  - `bench pip install -r apps/ferum_custom/requirements.txt`

## Portal

- Client portal pages are available under `/portal`:
  - List of Issues with SLA overdue highlight
  - Issue details with “Download Timesheet” and confirmation buttons

## CI / Tests

- GitHub Actions workflow (`.github/workflows/ci.yml`) installs the app and runs tests.
- Tests cover workflows and permission basics, including Client visibility by Customer.
