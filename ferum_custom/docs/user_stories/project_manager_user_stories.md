# Project Manager User Stories:

- 9.
- Story: Initiating a New Project – As a Project Manager, I want to create a new project when a contract is signed, so that I can start logging related service requests and documents under it.

### Details

- The PM receives contract details from sales.
- They then input it as a ServiceProject.

Acceptance Criteria:

### The PM can successfully fill in a form for ServiceProject

- select the Customer (if new, have sales or admin add the Customer first), set start/end dates, contract value, etc.
- They add all relevant ServiceObjects (if the client has multiple sites, they either select existing ones or create new ones on the fly).

When trying to add the same object twice, the form/validate prevents it.

- When saving, if an object is already linked to another active project, it throws an error and PM knows to investigate (maybe contract overlap).

- After creation, the project might be in a "Draft" or "Pending Approval" state.
- The PM triggers an action for approval (like notifying Director as above).

- Once approved and active, the PM sees it listed in their Projects list.
- They also see that a "welcome email" was sent to the client automatically (the PM might get CC’d or see a note in system).

The PM’s name is automatically set as project manager and they will receive notifications of events under this project.

Now the PM can proceed to log requests for this project.

- 10.
- Story: Logging a Service Request with Photos – As a Project Manager, I want to log a client’s maintenance request and attach initial photos, so that the issue is documented and can be assigned to an engineer.

Details: A client calls the PM directly and says there's a minor issue; the PM logs it.

Acceptance Criteria:

- PM navigates to "New Service Request", picks the Project (or Service Object) the issue relates to.
- The Customer auto-fills by project.

- They input the description provided by client.
- They mark priority normal (not emergency).

- The client also emailed some photos of the issue – the PM attaches those to the request (using attachment upload, which goes to Drive).

- The PM assigns a specific engineer (drop-down of active engineers; if filtering by region is in place, maybe it auto-filters relevant engineers).

- Saves the request.
- The system triggers a notification to the assigned engineer’s phone (Telegram bot says "New Request assigned: ...").

- The PM sees the request in "Open" status in the list.
- They call the engineer to ensure they saw it (double-check).

The attached photos are visible to the engineer via the bot or when they open the request in the system.

The request record shows all details and attachments correctly, and the PM can track it through to completion.

- 11.
- Story: Completing Work and Invoicing – As a Project Manager, I want to finalize a completed service request by generating the work report and preparing the client’s invoice, so that the client can be billed and the project records updated.

### Details

- Suppose the engineer finished the job and marked the request Completed, but PM needs to compile the formal report and get an invoice out.

Acceptance Criteria:

- PM sees an alert that ServiceRequest #123 is marked Completed by engineer and awaiting report (if engineer didn't do it).

- PM opens the request and clicks "Create Service Report".
- The system opens a new report form with the request linked (and maybe some info pre-filled like date, object).

### The engineer left notes via the bot, which the PM has; PM enters those as work items

- e.g., "Replaced 2 sprinkler heads - 2hrs labor".

The system auto-calculates cost if applicable (for internal records, maybe rate*hr) and sums it.

PM attaches a photo of the new parts installed that the engineer sent afterward.

- PM submits the ServiceReport.
- It's now official (and perhaps locked).

This triggers the ServiceRequest to change status to Completed/Closed automatically.

- PM then goes to the Invoicing module and creates a new Invoice for that project, period (maybe this job is billable separately).
- They link the ServiceReport or at least note "Services as per Work Report #123".

They enter the agreed amount (maybe it matches the contract or is an extra).

- Save the invoice.
- The Google Sheet updates, Admin is notified of the new invoice for client.

### PM then sends an email to the client via ERPNext

- selects the invoice and the report PDF and uses "Email" to send with a nice message.
- The client receives all documents.

### Acceptance

- The ServiceRequest now has a linked ServiceReport and an Invoice reference (maybe the Invoice doc references the project only, but PM can correlate).

- Later, PM sees the invoice was paid (Admin marked it Paid), and they see that reflected in the project’s financial summary (project now shows less receivable).

The client is satisfied, and the project records show the cycle from request to report to invoice all completed.
