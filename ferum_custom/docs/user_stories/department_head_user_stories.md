# Department Head (Service) User Stories:

- 7.
- Story: Approving a Service Request – As the Service Department Head, I want to review new service requests (especially high-priority ones) logged by office staff or clients, so that I can confirm resource allocation and approve work commencement.

### Details

- An office manager enters a request marked "Emergency".
- By process, it requires managerial approval to dispatch overtime maybe.

Acceptance Criteria:

- When a new ServiceRequest is created with high priority, the Dept Head receives a notification (perhaps email or sees it in an "Approvals" list).

- The Dept Head opens the request details, checks the description and the proposed assignment (or if none, assigns an engineer).

They change status from "New" to "Approved" or directly to "In Progress" after calling an engineer.

- The request then proceeds.
- The system could log that "Dept Head approved this emergency request at <time>".

- If the Dept Head is unavailable, an Admin could override or assign as well.
- But normally, the Dept Head should act within a short SLA for emergencies.

Acceptance: The engineer assignment is confirmed and the engineer got notified after Dept Head action (if not already).

- The Dept Head can see all requests in progress and their statuses on a dashboard to supervise (maybe a Kanban board of all open requests).

- 8.
- Story: Overseeing Work Reports – As the Service Department Head, I want to review completed ServiceReports to ensure quality and completeness before they go to the client, so that we maintain high service quality.

Details: Engineers submit ServiceReports with details of work done and maybe times.

Acceptance Criteria:

- Whenever a ServiceReport is submitted, it might be routed for review.
- Perhaps the Dept Head gets a notification or can see a list of "Reports pending approval".

They open the report, verify that the described work aligns with the issue and that all parts used are listed, etc.

- If something is missing (say an attachment like client-signed document isn't there), they could send it back or add a comment tagging the PM to fix it.

- If all good, they mark it as "Approved" (if such a status exists) or simply no action except informing the PM to send it to client.

The Dept Head's stamp of approval might be recorded (in comments or a field "verified_by_head = Yes").

This ensures process: e.g., "No ServiceReport goes out to client without Dept Head check".

### Acceptance

- For a sample report, if the engineer forgot to include a photo, the Dept Head can catch that and have it corrected before closure.
- The system allows editing (or adding attachments) to a submitted report by authorized persons (like Dept Head).

- Once reviewed, the Dept Head is satisfied that if the client sees this report, it meets standards.
- (Quality control achieved).
