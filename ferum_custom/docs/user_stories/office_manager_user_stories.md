# Office Manager User Stories:

- 15.
- Story: Recording an Incoming Call – As an Office Manager, I want to record a new service request that comes in via phone or email, so that it is properly logged and assigned in the system.

### Details

- A client calls the office to report an issue.
- Office Manager takes details.

Acceptance Criteria:

- Office Manager clicks "New Service Request".
- Selects the client or project based on caller (if not sure, can search by client name).

- Enters a concise subject and description as narrated by client.
- Possibly the client emails a photo afterward; the office manager can edit the request later to attach it.

Marks priority based on client tone (maybe normal).

- Since the office manager is not a tech expert, they leave it unassigned or assign to "Service Team" queue.
- The Department Head will assign an engineer soon.

- Saves the request.
- The system might notify Dept Head or PM that a new request from that client is logged.

- Office Manager gives the client a rough expectation (based on process, but the system could indicate e.g., "someone will contact you shortly").

- The request shows up in the system's list as Open, unassigned.
- It's visible to PMs.

### Acceptance

- The client is captured in the Customer field, linking the request properly.
- The office manager can see the request in the system with a unique ID to refer to.
- No manual sticky notes needed.

- If the client calls later for status, office manager can quickly search by client or request ID and update them (the timeline shows e.g., "Assigned to engineer, In Progress").

- 16.
- Story: Uploading a Contractor Invoice – As an Office Manager, I want to upload a subcontractor’s invoice and documents into the system, so that the accountant can process payment.

### Details

- A subcontractor sends their invoice and work act by email.
- Office manager handles data entry.

Acceptance Criteria:

Office Manager goes to the Invoices module, clicks New Invoice.

Selects the Project that this invoice relates to (or at least tags it).

Enters counterparty as the subcontractor's name (maybe they are also a "Supplier" in system or just free text).

Enters amount, month of service.

Attaches the scanned PDF of the invoice and act (upload to system, which goes to Drive).

In a custom field "Type" selects "Subcontractor Invoice".

- Saves.
- The Google Sheet updates with this entry (the office manager might not see that directly but knows it happens).

The Admin is notified of the new invoice (as earlier story).

The Office Manager also might inform the PM that the subcontractor bill came and is logged.

### Acceptance

- The subcontractor invoice record is visible to the Chief Accountant with all info and attachments, so they don't need the Office Manager to email them separately.
- The system thereby becomes the central store.

- Also, because the Office Manager created it and not the PM, the system highlights it (the sheet row is highlighted since not by PM, but that's expected because sometimes Office Manager does that for all projects).

- The Office Manager can later check that Admin marked it Paid after processing (to ensure the subcontractor will get paid on time, they could tell subcontractor "your payment is processed").
