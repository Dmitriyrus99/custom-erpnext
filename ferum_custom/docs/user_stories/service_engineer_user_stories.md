# Service Engineer User Stories:

- 12.
- Story: Receiving an Emergency Alert – As a Service Engineer, I want to be immediately alerted on my phone when an emergency service request is assigned to me, so that I can respond quickly.

### Details

- A request marked emergency is assigned to Engineer.
- The system should ping them.

Acceptance Criteria:

### Engineer’s Telegram bot (or WhatsApp) gets a loud notification

- e.g., "EMERGENCY New Request #77 at Client ABC, Fire alarm malfunctioning." including timestamp and maybe priority flag.

The message includes key details (address, contact person perhaps, since that could be in request description).

The engineer acknowledges either by clicking a quick "Acknowledge" button if provided or by sending a message back.

The system updates (maybe sets status to In Progress or at least logs that engineer responded at X time).

- The engineer prepares to go on-site, possibly clicking a link in the message that opens the request in the mobile view to see full details and attachments (like a photo of the control panel error if provided).

### Acceptance

- For an emergency created in test, the assigned engineer’s phone buzzes within seconds, they see the info needed, and the system logs their acknowledgement.

- 13.
- Story: Updating Job Status On-site – As a Service Engineer, I want to use the mobile bot to update the status of a service request when I start and finish work, so that the back-office knows the job’s progress without me having to call in.

Details: Engineer arrives on site, starts work, then completes.

Acceptance Criteria:

- Engineer sends "/start 77" via Telegram.
- Bot replies "Roger, Request 77 marked In Progress at 14:30." and the system sets the actual start time in ServiceRequest.

The service request’s status in ERPNext changes from Open to In Progress (visible to PM/Office).

### Later, engineer fixes the issue at 16

- 00 and sends "/done 77 Issue resolved.
- Replaced 2 sensors." (perhaps they can include a short note).

- The bot calls the API to mark Completed.
- If a ServiceReport is required first, the bot might say "Please provide work details to complete." (maybe it already got some text with the command).

### Assuming the system can auto-create a draft ServiceReport

- because the engineer included "Replaced 2 sensors." the system could create a ServiceReport with that in description and mark request Completed.
- If not automated, it might alert PM to do it.

But at least the status goes to Completed in the system, and actual end time is recorded.

### The bot confirms "Request 77 marked Completed at 16

- 05.
- Don’t forget to submit your work report."

- PM sees the update immediately.
- The engineer might then also use "/upload_photo 77" to send a "after fix" photo.

The bot attaches it and confirms.

### Acceptance

- The engineer didn't have to open a laptop or call in; via phone they updated status and attached evidence successfully, and the back-office can see real-time progress.

- 14.
- Story: Viewing Assigned Work – As a Service Engineer, I want to see a list of all open service requests assigned to me, so that I can plan and prioritize my tasks for the day.

Details: At the start of day, an engineer checks what tasks he has.

Acceptance Criteria:

- Engineer sends "/my_requests" command.
- Bot replies with something like: "You have 2 open requests:\n- #65 (Project X - routine maintenance) status: Open, due: Aug 12\n- - #77 (Client ABC - EMERGENCY) status: In Progress."

Alternatively, if using an app, the engineer logs in and sees a dashboard with their tasks listed by priority.

- They can select one to get details.
- For routine ones, maybe they schedule them later.

This helps them not forget any tickets.

### They can also query a specific request

- "/request 65" to get detail and possibly a location or contact from the description.

### Acceptance

- The list is accurate and up-to-date (if an issue was closed by someone else or reassigned, it no longer shows).

This fulfills requirement that engineers have quick visibility of their workload.
