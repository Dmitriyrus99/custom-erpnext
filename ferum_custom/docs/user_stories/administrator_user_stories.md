# Administrator User Stories:

1. Story: System Setup and Oversight – As an Administrator, I want to configure user accounts and monitor system activities, so that the right people have access and I can ensure everything runs smoothly.

### Details

- After initial deployment, the Admin creates accounts for all employees and assigns roles (e.g., mark certain users as Project Managers, Engineers, etc.).
- They configure integration credentials (enter the Telegram bot token, Google API keys into the settings).

Acceptance Criteria:

- The Admin can create a new user with a given role and that user can login and only see the modules they’re supposed to (verify a sample engineer account cannot view financial info).

- The Admin can see a dashboard of system status (e.g., via Prometheus/Grafana or ERPNext System Settings showing all scheduled jobs OK).

- When any critical event happens (like a failed backup or an integration error), the Admin receives a notification (e.g., via email or Sentry alert).
- For example, if Google Sheets update fails, an email is sent to Admin.

- The Admin can run an audit report that shows who did what in the last week (for instance, a log of all invoice status changes with user and timestamp).

- Admin can successfully perform a test restore on a staging environment using documented backup files to validate disaster recovery procedure.

- 2.
- Story: Invoice Approval Notification – As an Administrator, I want to be immediately notified when a Project Manager uploads a new subcontractor invoice, so that I can review and approve it for payment in a timely manner.

### Details

- A PM uses the system to record a new invoice from a subcontractor.
- As soon as they save it, the Admin is alerted.

Acceptance Criteria:

- Within a minute of the PM creating an Invoice record, the Admin’s Telegram bot (or email) receives a message with invoice key info.

The Admin can click a link in that message to open the invoice in ERPNext and review attachments.

- Only Admin (or Chief Accountant) can change its status to "Approved" or "Paid".
- If a PM tries to mark it paid, the system prevents it (permission denied).

- When Admin marks it "Paid", the status change is logged and (optionally) the PM gets a notification that the payment was processed (closing the loop).
