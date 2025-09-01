# Invoicing Module (Client Billing & Contractor Payments)

### Responsibilities

- Manage financial records of outgoing invoices to clients and incoming payable invoices from subcontractors, along with relevant integrations to accounting sheets and notifications.

### DocTypes

- Invoice (custom DocType managed mostly via custom app logic).
- Possibly separate docTypes or a field to distinguish Invoice (Client) vs Bill (Subcontractor), but the design suggests using one doctype with a “counterparty type” field.

Key Fields:

### Invoice

- project (Link to ServiceProject, nullable if an invoice isn’t tied to a project, but in this domain usually it is), period or invoice_date, amount, currency, counterparty_name (the client or subcontractor name, could be Link to Customer or a separate field), counterparty_type (maybe values “Customer” or “Subcontractor”), description (text like billing description or payment basis), status (Draft, Sent, Paid, etc.), attachments (could be a table of CustomAttachment or just file links).

- Additionally, fields like tax_applicable (checkbox if VAT invoice), paid_date, etc.
- can be present for tracking.

Automation & Hooks:

### On Invoice validate/submit

- ensure required fields are present (project, amount, counterparty, period).
- For a client invoice, perhaps ensure there’s at least one ServiceReport or some basis (not strictly enforced by system but by process).

### On Invoice after_insert (creation)

- Integrate with Google Sheets.
- A hook or external call will take the new invoice’s data and append a row in the Google Sheet.
- This could be done by a background job to not slow the form save.
- The data likely includes Project name, Month, Amount, Counterparty, EnteredBy.
- The Sheets integration also might do things like highlight the row if conditions are met (the logic of highlighting if created by someone not the project’s PM could either be handled by an Apps Script in the sheet or by setting a cell value that triggers conditional formatting).

### Possibly on Invoice on_change_status (whenever status field is changed)

- If status = "Paid", maybe update something in the Google Sheet (mark that row as paid, maybe via a checkbox or date column).
- This could also be done manually by accountant in the sheet, depending on desired sync direction (one-way vs two-way).
- The spec doesn’t explicitly say updating sheet on status change, but it would be logical to reflect payments in the tracking sheet as well.

- The Invoice doctype might not heavily use ERPNext workflows, because approvals (like director approval of payments) might be done offline or simply by role restrictions.

Permissions & Workflow:

### Only certain roles can create invoices

- Project Managers for client invoices (for their projects), Office Managers for maybe any project (since they might help in data entry), and perhaps Accountants can create any.

- Only Admin/Chief Accountant can mark an invoice as Paid (to ensure segregation of duties).
- This could be enforced by a combination of role permission (field-level permission on status field) or by providing a separate doctype or tool to set status.

- The General Director’s approval for big invoices might be outside the system (signing the physical document).
- However, the system could have a field “approved_by_director” that an Admin checks once they have the signed paperwork.
- It’s not specified, but could be a feature to log approvals.

Integrations:

### Google Sheets

- As described, a central part of this module.
- The sheet not only logs the invoices but also does calculations: summing totals per project and highlighting anomalies.
- The integration likely uses a service account with Google API credentials stored in the backend (protected).
- It must handle network errors or Google API errors gracefully (retry or alert).

### Google Drive

- All invoice-related documents (scans of signed acts, scans of subcontractor invoices, etc.) are stored on Drive.
- The Invoice record might just contain links to these in the attachments or in a field.
- Possibly the user uploads those via ERPNext, which then sync to Drive like other attachments.

### Email

- When an invoice is created, an email could be sent to the client with the invoice attached (if emailing invoices is desired; otherwise, the PM handles it manually).
- More critically, an email notification to Admin on a new subcontractor invoice is implemented.
- This could be via an ERPNext notification rule or via a server event that sends an email/Telegram message to the Admin user: “New subcontractor invoice for Project X, amount Y has been uploaded by PM Z.”

### Telegram Bot

- Possibly, admins could query invoice status via the bot or be notified via the bot as well as email.
- The spec explicitly mentions Telegram notification to Admin on new invoice upload.

### Accounting System

- Currently, invoicing here is standalone.
- However, if the company uses external accounting (1C), double-entry might happen there.
- In the future, an integration might export invoice data to 1C or generate an XML/CSV that 1C can import, to avoid manually re-entering invoices in the accounting system.
- This isn’t implemented yet but noted as a possibility.

API Endpoints: The custom backend could expose:

GET /invoices – list invoices (maybe filter by project or status).

- POST /invoices – create an invoice (though internal users likely use ERPNext UI, an external endpoint might be used by a React interface for Office Manager to upload a bunch of subcontractor invoices quickly).

PUT /invoices/{id} – update (for marking paid).

- These endpoints would ensure only authorized roles (with valid JWT tokens) can call them.
- They encapsulate the logic of also updating Google Sheet, etc.

- Given the heavy internal nature of invoices, these endpoints might primarily serve a custom UI rather than external clients.

UI Components:

- ERPNext Form for Invoice (if implemented as a DocType in ERPNext).
- Possibly they manage it outside ERPNext’s desk, but since it’s easier to use ERPNext’s forms, it might be created as a DocType in the custom app so that PMs can use the desk UI to create invoices.
- This form would have attachments section to upload scans.
- It might have a custom script to enforce that certain fields appear/disappear based on counterparty type (e.g., hide VAT field if subcontractor is self-employed with no VAT).

- A Google Sheet accessible to accountants and managers, used as a report/dashboard for all invoices.
- This is an external UI but important.

- A custom React component (optional) that could embed the Google Sheet or present invoice data in a user-friendly grid.
- But likely, the sheet suffices for now.

### Reporting

- maybe an “A/R Report” in ERPNext showing all unpaid client invoices or “Cost Report” for all subcontractor payments by project.

- This module improves financial transparency – every invoice is logged and visible to management in real-time via the sheet, and it closes the loop from service delivery to cash flow.
- It also aids in ensuring subcontractors are paid on time and their costs are tracked against projects.
