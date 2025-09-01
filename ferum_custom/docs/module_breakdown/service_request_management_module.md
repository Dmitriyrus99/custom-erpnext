# Service Request Management Module

### Responsibilities

- Handle the end-to-end lifecycle of service tickets (maintenance requests), from creation to closure.
- This includes assignment, status tracking, and notifications.

### DocTypes

- ServiceRequest, plus child table RequestPhotoAttachmentItem.
- (Also utilizes CustomAttachment for storing the actual files referenced by attachment items.)

Key Fields:

### ServiceRequest

- title (or subject), description, type (Choice: e.g., "Routine Maintenance", "Emergency"), priority (could be derived from type or separate field), service_object (Link to ServiceObject, optional but fills project/customer if used), project (Link to ServiceProject, optional – if the request isn’t under a contract, it might be blank), customer (Link to Customer, auto from object or project), status (Workflow: e.g., Open, In Progress, Completed, Closed, Cancelled), assigned_to (Link to Employee/User for the engineer), reported_datetime, actual_start_datetime, actual_end_datetime, linked_report (Link to ServiceReport, set once work report is submitted).

RequestPhotoAttachmentItem: attachment (Link to CustomAttachment) and perhaps a caption or timestamp.

Automation & Hooks:

### Client Script (form level)

- When a user selects a ServiceObject on the form, a script automatically sets the project and customer fields based on that object.
- It likely does a lookup (frappe call) to fetch the associated project of that object and fills it in, ensuring the request is tied correctly.
- It may also filter the assigned_to field options (e.g., only show engineers in the same region or available).

Server Scripts:

### On ServiceRequest validate

- enforce workflow rules.
- A custom method _validate_workflow_transition likely checks that status changes are logical (e.g., can’t skip stages).
- Also, it ensures that setting status to Completed/Closed is only allowed if linked_report is not null.
- If that condition fails, it throws an error reminding to attach a ServiceReport first.

### Before save or on update

- if status is being set to Completed and actual_end_datetime is empty, auto-set actual_end_datetime = now.
- Similarly, when moving from Open to In Progress, could set actual_start_datetime if not set.

### A calculation (perhaps on update)

- compute turnaround time.
- If both reported_datetime and actual_end_datetime are present, calculate difference in hours/days and store in a field duration_hours.
- This happens either on save or via a background job.

Notifications:

- On submit (creation) of a new ServiceRequest, trigger notifications.
- This can be done via ERPNext Notification doctype or via hooks.
- For example, in hooks.py a notification could be configured: doc_events: { "Service Request": { "after_insert": send_new_request_alert } }.
- The send_new_request_alert would then implement logic: if request is emergency, notify on-call group (Telegram bot message, perhaps using the bot API); for any new request, email assigned engineer and PM, and if the request was client-created, email the client a confirmation.
- These messages include key details (issue description, assigned engineer name, expected schedule).

- On status change events, similar notifications can fire.
- E.g., when an engineer marks Completed, notify PM or client that work is done.

### Escalation

- a scheduled task might daily check for any open requests older than X days (especially emergencies older than a few hours) and send reminders to the assignee and CC managers.

### on_trash (if allowed at all)

- likely restricted – only Admin can delete/cancel a ServiceRequest.
- If deleted, system should also perhaps delete linked attachments or orphan data, but normally requests would be canceled rather than deleted.

Integrations & API:

REST API Endpoints: The custom backend exposes endpoints for external interactions:

- POST /requests – Create a new request.
- Used by the Telegram/WhatsApp bot or a client portal.
- This endpoint requires authentication (the bot passes a token or the user logs in via the portal) and then internally creates the ServiceRequest via Frappe API.

- GET /requests – List requests with filters.
- For instance, an engineer can retrieve their open requests (?assigned_to=<my_id>&status=Open), or a client can list all requests for their projects (the backend filters by user’s customer).

GET /requests/{id} – Get details of one request, including attached photos and linked report.

PUT /requests/{id} – Update a request (e.g., edit description or change assignment).

- PUT /requests/{id}/status – A specialized endpoint for status updates, which enforces the same workflow rules as the server script.
- This is what the bot uses when an engineer sends a command like /set_status 123 Completed – the backend checks that user is indeed assigned to request 123 and that moving to Completed is allowed, then updates the doc.

Bot Commands: As outlined earlier, the Telegram bot is tightly integrated:

/new_request <desc> for clients – triggers POST /requests.

/my_requests for engineers – triggers GET /requests?assigned_to=me.

/set_status <req> <status> – triggers the status update endpoint.

- /upload_photo <req> – the bot listens for an image and then calls an API (perhaps POST /requests/{id}/attachments) to attach the photo.
- The backend then creates a CustomAttachment and RequestPhotoAttachmentItem record linking it.

- The bot uses Telegram user authentication mapped to a system user (there might be a pre-registration such that the bot knows Telegram user X corresponds to ERPNext user Y).
- Only authorized commands are executed.

### Email Integration

- The system might also allow creating a request via email (e.g., a client emails a support address).
- ERPNext can catch incoming emails and create a document.
- This isn’t detailed in the spec, but could be a future consideration.

### Google Calendar

- Mentioned as a potential integration, if an event needs scheduling.
- For example, when a request is set to In Progress with a planned start time, a Google Calendar event could be created for the engineer.
- This is not core functionality but an idea for keeping schedules.

UI Components:

- ERPNext Kanban Board or list for Service Requests by status, which the service team can use to track progress (e.g., a Kanban with columns New, In Progress, Completed, providing a visual workflow).

### A custom Engineer Dashboard

- showing an engineer only his assigned open tasks, possibly with quick action buttons to update status.

### Client Portal Page

- where a logged-in client can create a request and view the status of existing ones.
- This could be achieved with ERPNext’s portal or the external React app.
- It will ensure they only see their own data via permission rules.

- This module thus ensures timely logging of issues, proper assignment and resolution tracking, and high visibility through notifications and status updates.
- By integrating with messaging apps, it extends the reach of the ERP to field personnel and clients in a convenient way.
