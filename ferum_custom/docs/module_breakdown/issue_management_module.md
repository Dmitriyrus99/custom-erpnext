# Issue Management Module

### Responsibilities

- Handle the end-to-end lifecycle of service tickets (maintenance issues), from creation to closure.
- This includes assignment, status tracking, and notifications.

### DocTypes

- Issue.
- (Also utilizes CustomAttachment for storing the actual files referenced by Issue).

Key Fields:

### Issue

- subject, description, issue_type (Choice: e.g., "Routine Maintenance", "Emergency"), priority (could be derived from type or separate field), asset (Link to Asset, optional but fills project/customer if used), project (Link to Project, optional – if the issue isn’t under a contract, it might be blank), customer (Link to Customer, auto from asset or project), status (Workflow: e.g., Open, In Progress, Resolved, Closed, Cancelled), assigned_to (Link to Employee/User for the engineer), creation, resolution_date, linked_timesheet (Link to Timesheet, set once timesheet is submitted).

Automation & Hooks:

### Client Script (form level)

- When a user selects an Asset on the form, a script automatically sets the project and customer fields based on that asset.
- It likely does a lookup (frappe call) to fetch the associated project of that asset and fills it in, ensuring the issue is tied correctly.
- It may also filter the assigned_to field options (e.g., only show engineers in the same region or available).

Server Scripts:

### On Issue validate

- enforce workflow rules.
- A custom method \_validate_workflow_transition likely checks that status changes are logical (e.g., can’t skip stages).
- Also, it ensures that setting status to Resolved/Closed is only allowed if linked_timesheet is not null.
- If that condition fails, it throws an error reminding to attach a Timesheet first.

### Before save or on update

- if status is being set to Resolved and resolution_date is empty, auto-set resolution_date = now.
- Similarly, when moving from Open to In Progress, could set start_date if not set.

### A calculation (perhaps on update)

- If both creation and resolution_date are present, calculate difference in hours/days and store in a field duration_hours.
- This happens either on save or via a background job.

Notifications:

### On submit (creation) of a new Issue, trigger notifications.
- This can be done via ERPNext Notification doctype or via hooks.
- For example, in hooks.py a notification could be configured: doc_events: { "Issue": { "after_insert": send_new_issue_alert } }.
- The send_new_issue_alert would then implement logic: if issue is emergency, notify on-call group (Telegram bot message, perhaps using the bot API); for any new issue, email assigned engineer and PM, and if the issue was client-created, email the client a confirmation.
- These messages include key details (issue description, assigned engineer name, expected schedule).

- On status change events, similar notifications can fire.
- E.g., when an engineer marks Resolved, notify PM or client that work is done.

### Escalation

- a scheduled task might daily check for any open issues older than X days (especially emergencies older than a few hours) and send reminders to the assignee and CC managers.

### on_trash (if allowed at all)

- likely restricted – only Admin can delete/cancel an Issue.
- If deleted, system should also perhaps delete linked attachments or orphan data, but normally issues would be canceled rather than deleted.

Integrations & API:

### REST API Endpoints: The custom backend exposes endpoints for external interactions:

- POST /issues – Create a new issue.
- Used by the Telegram/WhatsApp bot or a client portal.
- This endpoint requires authentication (the bot passes a token or the user logs in via the portal) and then internally creates the Issue via Frappe API.

- GET /issues – List issues with filters.
- For instance, an engineer can retrieve their open issues (?assigned_to=<my_id>&status=Open), or a client can list all issues for their projects (the backend filters by user’s customer).

GET /issues/{id} – Get details of one issue, including attached photos and linked timesheet.

PUT /issues/{id} – Update an issue (e.g., edit description or change assignment).

- PUT /issues/{id}/status – A specialized endpoint for status updates, which enforces the same workflow rules as the server script.
- This is what the bot uses when an engineer sends a command like /set_status 123 Resolved – the backend checks that user is indeed assigned to issue 123 and that moving to Resolved is allowed, then updates the doc.

Bot Commands: As outlined earlier, the Telegram bot is tightly integrated:

- /new_issue <desc> for clients – triggers POST /issues.

- /my_issues for engineers – triggers GET /issues?assigned_to=me.

- /set_status <issue> <status> – triggers the status update endpoint.

- /upload_photo <issue> – the bot listens for an image and then calls an API (perhaps POST /issues/{id}/attachments) to attach the photo.
- The backend then creates a CustomAttachment record and links it to the Issue directly.

- The bot uses Telegram user authentication mapped to a system user (there might be a pre-registration such that the bot knows Telegram user X corresponds to ERPNext user Y).
- Only authorized commands are executed.

### Email Integration

- The system might also allow creating an issue via email (e.g., a client emails a support address).
- ERPNext can catch incoming emails and create a document.
- This isn’t detailed in the spec, but could be a future consideration.

### Google Calendar

- Mentioned as a potential integration, if an event needs scheduling.
- For example, when an Issue is set to In Progress with a planned start time, a Google Calendar event could be created for the engineer.
- This is not core functionality but an idea for keeping schedules.

UI Components:

- ERPNext Kanban Board or list for Issues by status, which the service team can use to track progress (e.g., a Kanban with columns New, In Progress, Resolved, providing a visual workflow).

### A custom Engineer Dashboard

- showing an technician only his assigned open issues, possibly with quick action buttons to update status.

### Client Portal Page

- where a logged-in client can create an issue and view the status of existing ones.
- This could be achieved with ERPNext’s portal or the external React app.
- It will ensure they only see their own data via permission rules.

- This module thus ensures timely logging of issues, proper assignment and resolution tracking, and high visibility through notifications and status updates.
- By integrating with messaging apps, it extends the reach of the ERP to field personnel and clients in a convenient way.
