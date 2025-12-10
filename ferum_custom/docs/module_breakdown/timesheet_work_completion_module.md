# Timesheet & Work Completion Module

### Responsibilities

- Document the completion of work via Timesheets and handle the linkage between completed work and resolving issues.
- This module also covers any quality control steps and integration with Drive for storing completed reports.

DocTypes: Timesheet, Time Log (child).

Key Fields:

### Timesheet

- issue (Link to Issue), start_date, end_date, status (Draft/Submitted), total_hours (calculated), comments/remarks, possibly a field for “signed_by_client” (Yes/No or date).

### Time Log

- description, hours, activity_type.

Automation & Hooks:

### On Timesheet before_save

- calculate total hours.
- Sum up all hours in the Time Log table.
- This populates Timesheet.total_hours field.

### On Timesheet validate

- ensure at least one time log is present and filled out.
- Ensure any mandatory fields (like start_date) are set.

### On Timesheet on_submit:

- Link to Issue: set the corresponding Issue.linked_timesheet = this timesheet’s name.

### Change Issue status

- if not already Resolved, set it to Resolved (or perhaps directly Closed).
- This might use the Issue API or a direct DB update; however, safer to call a function to transition the status respecting workflow (the spec suggests it automatically marks Resolved upon timesheet submission).

### Trigger notification

- notify the project manager or admin that a new timesheet has been submitted (so they can review or send to client).

### Optionally, auto-email the timesheet to client

- If configured, on submit the system could generate PDF and send email to client with a thank you/note that “Work is completed, see attached timesheet.”.

### Drive upload

- If the timesheet has attachments (like photos or signed scans), an integration could run (either on_submit or via a scheduled job soon after) to push those files to Google Drive.
- The spec mentions possibly doing this in background and storing the Drive link in the CustomAttachment.

### On Timesheet on_update (after submit)

- If any changes or additional attachments are added (in case where they allow adding attachments post submission through amendment or a separate mechanism), ensure those files also sync to Drive.

### On Issue side

- The submission of a Timesheet should fulfill the requirement that allowed the Issue to be closed.
- Possibly, once the Timesheet is submitted, an automated rule could mark the Issue status from Resolved to Closed.
- Or if a Timesheet is cancelled (unlikely scenario, perhaps if created in error), the system should clear the linked_timesheet on the Issue and possibly reopen the issue status if it was closed.

### REST API Endpoints: Similar to issues, for external use (like the bot):

GET /timesheets – list Timesheets (with filters like project or date).

GET /timesheets/{id} – details of a specific timesheet, including its time logs and attachments.

- POST /timesheets – create a Timesheet.
- In practice, engineers might usually use the ERPNext UI for this (since it’s easier to input multiple lines), but having an API allows a mobile interface or the bot to create a simple timesheet.
- For example, the bot might allow an engineer to mark an issue done and provide a short summary, which could create a minimal Timesheet record for them.

- There might not be a direct need for PUT /timesheets (editing a timesheet via API) as that would typically be done in the system UI by managers.

Google Drive: As discussed, integration to upload attachments to Drive upon report submission.

### Email

- ability to email the report from the system (likely through an ERPNext email alert or a button that triggers a frappe.sendmail).

### Printing

- The module ensures a custom print format for ServiceReport is available, making printed or PDF versions look professional (company logo, formatted tables of work done, signature lines, etc.).

### UI Components

- ERPNext Form for Timesheet – includes one child table for time logs.
- It might have custom client scripts to facilitate input (e.g., if opened via an Issue, auto-fill certain info as context).

Print Format template for the Timesheet for PDF/print output.

Listing of Timesheets per project or in a central view for admins to track all completed work.

- This module ensures every job is formally closed with documentation.
- The hooks guarantee data consistency (timesheet totals and linkages), and the integration with Drive/Email ensures that internal and external stakeholders get the paperwork they need without hassle.
