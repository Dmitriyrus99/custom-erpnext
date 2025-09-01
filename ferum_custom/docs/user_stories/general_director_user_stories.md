# General Director User Stories:

- 3.
- Story: Approving a New Contract – As the General Director, I want to review and approve any new service contract (project) created, so that no project starts without top-level consent.

### Details

- A sales manager indicates a contract is won.
- The PM creates a ServiceProject record and sets it to "Pending Approval" status.
- The Director then reviews the details.

Acceptance Criteria:

The Director is notified (via bot or email) when a new ServiceProject is awaiting approval.

The Director can log in and see the project details (client, contract value, duration, included sites).

- There is an "Approve" action available (maybe a button or just setting status to Active).
- Director clicks Approve.

- After approval, the project status becomes "Active", and relevant parties (PM, maybe client via a welcome email) are automatically informed.

The system logs that "Director X approved project Y on date/time".

- If the Director rejects or needs changes, they can leave a comment or set status to "Needs Revision", which triggers a notification back to the PM.

- 4.
- Story: Viewing KPI Summary – As the General Director, I want to quickly check key performance indicators of the service operations, so that I have an overview of company performance without digging into details.

### Details

- The Director might not use the ERP daily, but occasionally wants metrics: open requests count, average closure time, revenue vs costs, etc.

Acceptance Criteria:

The Director can send a command to the Telegram bot (like /analytics) and receive a nicely formatted summary of metrics.

### For example, "Current Open Requests

- 3 (Avg Age: 5 days)\nThis Month Completed Requests: 20 (95% on-time)\nActive Projects: 5 (2 at risk of delay)\nReceivables: $50k (overdue: $5k)\nMonth Revenue: $100k, Costs: $60k (Profitability 40%)."

- Alternatively, the Director can open an "Analytics Dashboard" in the ERPNext UI showing charts for some of these metrics.
- The data should match the latest info (maybe cached within last few hours).

- The Director must not see raw data beyond their interest (the interface should present it at summary level, with ability to drill down if needed).

### Security

- This info should only be accessible to Director and Admin, not other roles, ensuring confidentiality of financials.
