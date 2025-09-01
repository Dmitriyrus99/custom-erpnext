# Work Report & Completion Module

### Responsibilities

- Document the completion of work via Service Reports and handle the linkage between completed work and closing service requests.
- This module also covers any quality control steps and integration with Drive for storing completed reports.

DocTypes: ServiceReport, ServiceReportWorkItem (child), ServiceReportDocumentItem (child).

Key Fields:

### ServiceReport

- service_request (Link to ServiceRequest), report_date (date of completion), status (Draft/Submitted), total_amount (calculated), comments/remarks, possibly a field for “signed_by_client” (Yes/No or date).

### ServiceReportWorkItem

- description, quantity, unit, rate or cost, amount.
- Possibly a link to an item code if they track standardized tasks or parts.

ServiceReportDocumentItem: attachment (Link to CustomAttachment), doc_name or type (e.g., “Signed Act scan”).

Automation & Hooks:

### On ServiceReport before_save

- calculate total.
- Sum up all amount in the WorkItem table, or if rate * quantity, ensure each line’s amount is computed, then sum.
- This populates ServiceReport.total_amount field.

### On ServiceReport validate

- ensure at least one work item is present and filled out.
- Ensure any mandatory fields (like report_date) are set.

On ServiceReport on_submit:

Link to ServiceRequest: set the corresponding ServiceRequest.linked_report = this report’s name.

### Change ServiceRequest status

- if not already Completed, set it to Completed (or perhaps directly Closed).
- This might use the ServiceRequest API or a direct DB update; however, safer to call a function to transition the status respecting workflow (the spec suggests it automatically marks Completed upon report submission).

### Trigger notification

- notify the project manager or admin that a new report has been submitted (so they can review or send to client).

### Optionally, auto-email the report to client

- If configured, on submit the system could generate PDF and send email to client with a thank you/note that “Work is completed, see attached report.”.

### Drive upload

- If the report has attachments (like photos or signed scans), an integration could run (either on_submit or via a scheduled job soon after) to push those files to Google Drive.
- The spec mentions possibly doing this in background and storing the Drive link in the ServiceReportDocumentItem.

### On ServiceReport on_update (after submit)

- If any changes or additional attachments are added (in case where they allow adding attachments post submission through amendment or a separate mechanism), ensure those files also sync to Drive.

### On ServiceRequest side

- The submission of a ServiceReport should fulfill the requirement that allowed the ServiceRequest to be closed.
- Possibly, once the ServiceReport is submitted, an automated rule could mark the ServiceRequest status from Completed to Closed.
- Or maybe they leave it as Completed until client confirmation, which could be an extra step (not coded, but a process).

- If a ServiceReport is cancelled (unlikely scenario, perhaps if created in error), the system should clear the linked_report on the ServiceRequest and possibly reopen the request status if it was closed.
- This would require a custom hook on report cancel (ERPNext calls on_cancel) to handle that.

Integrations & API:

REST API Endpoints: Similar to requests, for external use (like the bot):

GET /reports – list ServiceReports (with filters like project or date).

GET /reports/{id} – details of a specific report, including its work items and attachments.

- POST /reports – create a ServiceReport.
- In practice, engineers might usually use the ERPNext UI for this (since it’s easier to input multiple lines), but having an API allows a mobile interface or the bot to create a simple report.
- For example, the bot might allow an engineer to mark a request done and provide a short summary, which could create a minimal ServiceReport record for them.

- There might not be a direct need for PUT /reports (editing a report via API) as that would typically be done in the system UI by managers.

Google Drive: As discussed, integration to upload attachments to Drive upon report submission.

### Email

- ability to email the report from the system (likely through an ERPNext email alert or a button that triggers a frappe.sendmail).

### Printing

- The module ensures a custom print format for ServiceReport is available, making printed or PDF versions look professional (company logo, formatted tables of work done, signature lines, etc.).

UI Components:

- ERPNext Form for ServiceReport – includes two child tables for work items and attachments.
- It might have custom client scripts to facilitate input (e.g., if opened via a ServiceRequest, auto-fill certain info as context).

- Possibly a dedicated page or dialog to quickly create a report from a request (the “Complete Request” action might bring up a simplified form to enter work done).

Print Format template for the ServiceReport for PDF/print output.

Listing of ServiceReports per project or in a central view for admins to track all completed acts.

- This module ensures every job is formally closed with documentation.
- The hooks guarantee data consistency (report totals and linkages), and the integration with Drive/Email ensures that internal and external stakeholders get the paperwork they need without hassle.
