# User Roles and Permissions Matrix

- The system defines a clear set of user roles, each with specific permissions corresponding to their job functions.
- Below is an overview of each role and the actions they are allowed to perform.
- A matrix of roles vs.
- modules/actions is summarized afterward to highlight who can do what.

### Administrator

- Top-level control.
- The Admin has full access to all records (projects, requests, reports, invoices, HR, logs).
- They manage user accounts and role assignments.
- Administrators are the ones to receive critical system notifications, for example when a new invoice is uploaded or if an error occurs in a scheduled task.
- They also have exclusive rights to certain actions like changing an invoice status to “Paid” (closing financial records).
- In analytics, Admin can query any KPI or see any dashboard via the bot or ERPNext desk.

### General Director (CEO)

- The highest approval authority in the business workflow.
- The Director’s primary actions in the system are to approve or sign off on major records: they approve budgets, all outgoing payments, and contracts before they become active.
- In practice, this might mean the Director is notified when a new contract (ServiceProject) is created and needs their sign-off, or when a payroll or large invoice is prepared.
- The Director likely has read access to everything, but limited edit rights – they wouldn’t create records, but they might change a status to “Approved” on a contract or invoice.
- They also would use analytics (via bot) to get high-level reports (like financial metrics).

### Chief Accountant

- Responsible for financial records and compliance.
- The Chief Accountant can manage Invoice records (especially marking subcontractor invoices as paid, and verifying client invoices).
- They also handle PayrollEntryCustom entries – creating and submitting payrolls.
- This role has read access to projects, requests, and reports, but primarily to understand context for billing and payroll.
- The accountant ensures tax-related fields are correct (e.g., marking VAT if needed) and can generate necessary financial reports from the data.
- They have permission to view and modify any financial data (invoices, payroll) and likely read access to all attachments.
- They might not edit ServiceRequests or Projects (beyond perhaps viewing them for context).

### Department Head – Sales/Procurement (and Service Department Head)

- This can be considered two roles if separated, but they share a similar level of permission.
- These roles oversee their respective domains.
- For Service Department Head, they supervise service operations: they can approve new ServiceRequests (if an office manager logs a request, it might wait for head approval), oversee engineers, and review ServiceReports.
- They have rights to change statuses on requests (e.g., they could close a request or reopen it if needed) and possibly to assign engineers.
- They also might approve timesheets or resource allocation.
- For Sales/Procurement Head, they would be involved in contract approvals and any subcontractor agreements – hence, they can approve ServiceProjects (maybe set status Active post-director approval) and oversee subcontractor performance.
- Both types of Department Heads have broad read access across the system to monitor progress and performance, but write access mainly for approvals and oversight tasks.

### Project Manager

- A central operational role.
- Project Managers (PMs) can create and edit ServiceProjects (for projects they manage), including adding service objects.
- They manage ServiceRequests for their projects – they can create requests, assign them, update statuses (especially marking them completed once ServiceReports come in).
- They also handle ServiceReports: while engineers might draft them, PMs often review and submit them (or in some cases PM creates the report if engineer is not using the system directly).
- Importantly, PMs upload Invoice records for both clients and subcontractors related to their projects.
- They do not approve payments (that’s for admin/accountant), but they mark when an invoice is ready (maybe “Pending Approval” status).
- They also upload attachments (photos, docs) as needed.
- PMs have access to Google Drive through the integration to place files for their projects.
- They are likely given permission to see all data for projects they lead, but not necessarily other projects (unless there's a need).
- They also interface with clients via the system (could use the client portal on behalf of client sometimes).
- Their permissions are extensive in the Projects, Requests, Reports, Invoices modules, but limited in HR or other projects not assigned to them.

### Service Engineer

- Field technicians who execute the work.
- Engineers have more limited access: they can view ServiceProjects they are assigned to (or generally all active projects? But likely just their scope), they can see and update ServiceRequests assigned to them.
- They would not see others’ requests except maybe in a limited way (or if they need to pick up unassigned ones, this depends on design).
- They can change status on their requests (Open -> In Progress -> Completed) but likely cannot Close (that might be reserved for PM or Admin).
- They can create ServiceReports for their completed tasks – at least draft them, including adding work items and photos.
- Submission of the report might require a PM or engineer can do it; spec indicates engineer or PM can submit.
- Engineers have upload rights for attachments on their requests (photos, etc.).
- They do not have access to invoices or HR modules.
- They likely can’t create projects or see financial info like contract values or payments.
- Essentially, their UI could be a simplified portal or the mobile bot interface showing them just what they need to do their job.

### Office Manager

- An administrative support role managing documentation and initial data entry.
- Office Managers can log incoming ServiceRequests (e.g., when a client calls the office, they create the ticket in the system).
- They also prepare ServiceReports if an engineer gives them info or paperwork (some companies have office staff type up reports from field notes).
- Additionally, they have permissions to create Invoice records and upload invoice documents across all projects (since they often handle paperwork, they might assist any PM in entering an invoice into the system or scanning documents).
- They have broad read access to everything except maybe HR (they wouldn’t see payroll except maybe their own if they are an employee).
- They can view all projects and requests to route information correctly.
- They do not typically alter statuses beyond maybe an initial triage status on requests.
- This role exists to support both the service and accounting departments by ensuring data (requests, acts, invoices) is entered and filed.

### Client (Customer)

- External user role with highly restricted access.
- A Client can log into a web portal (or use the chat bot) to interact with the system.
- They can view their own projects (probably a limited view showing project status and basic info).
- They can create new ServiceRequests for their equipment and check the status of existing requests.
- They might also be able to download their documents (like the signed ServiceReport or invoices related to them).
- They cannot see internal data like other clients’ info, costs, or any invoices that the company internally uses (they might see the invoice that was addressed to them, but not ones to subcontractors).
- Financial figures such as contract value might or might not be visible to them (since they are the client, they know the contract value from the contract itself, so showing it in the portal could be fine; but maybe hide internal costs).
- The system enforces record-level security: any document has a “Customer” field is only accessible to the user if it matches their linked customer profile.
- This is achieved with ERPNext’s user permissions or query conditions (so each client user is only permitted to their own records).

### Record-Level and Field-Level Permissions

- The system uses ERPNext’s permission engine to enforce who can read/write each DocType:

### All DocTypes (Project, Request, Report, Invoice, Attachment)

- Role permissions define create/read/write for each role.
- For instance, ServiceRequest:

Create: Project Manager, Office Manager, Client (with restrictions), Admin.

Read: All internal roles (maybe engineer only if assigned or if project member), Client (only their requests).

### Write

- Engineer (their assigned requests partially, like status only), PM (requests in their projects), Department Head, Admin.

Submit (if using submit workflow): Engineer or PM can submit ServiceReport, etc.

ServiceProject:

Create: PM, Admin.

### Read

- PM (their projects), Dept Head, Admin, maybe Office Manager (all, to allow linking in requests), Client (their projects only).

Write: PM (their projects), Dept Head (maybe to approve or edit), Admin.

ServiceReport:

Create: Engineer or PM for relevant request.

Read: PM, Engineer (if related), Dept Head, Admin, Client (maybe could view final report doc if we expose it).

Write: Engineer/PM until submit; after submit, only Admin or PM can cancel/amend.

Invoice:

Create: PM, Office Manager, Admin.

Read: Admin, Accountant, PM (their projects’ invoices), maybe Dept Head (for oversight).

### Write

- Admin and Accountant (especially for status field).
- PM might be allowed to edit before it’s marked approved.

- Clients do not have access to Invoice records in the system – they get their invoice via email or so, but they don’t see internal invoice tracking.

PayrollEntryCustom:

Create/Read/Write: Chief Accountant (and Admin).

No access at all for others (even directors might just get a summary outside system).

CustomAttachment / attachments:

### Read/Download

- if you can read the parent, you can get the attachment.
- Clients can download their own attachments (like a report PDF).

### Write/Delete

- only roles with write on parent doc, or admin, can delete an attachment.
- So an engineer might add but not delete attachments once added, depending on config.

A permissions matrix can be depicted as:

Role →	Admin	Director	Accountant	Dept Head (Service/Sales)	Project Manager	Engineer	Office Manager	Client

- Projects (ServiceProject)	C/R/W (all)	R (approve)	R	R/W (approve)	C/R/W (own)	R (assigned)	R	R (own)
Service Objects	C/R/W	R	R	R	C/R/W (as part of project)	R (if needed)	R	(n/a)
Service Requests	C/R/W (all)	R (monitor)	R	R (oversight)	C/R/W (for projects)	R/W (status for assigned)	C/R (all projects)	C/R (own)
Service Reports	C/R/W (all)	R	R	R (review)	C/R/W (projects)	C/R (create for own tasks)	R	R (their projects’ final report)
Attachments	R/W (all)	R	R	R	R/W (for their projects)	C/R (add photos)	C/R/W (docs for any project)	R (download files of their own projects/requests)
Invoices	C/R/W (all)	R (approve payments)	C/R/W (financials)	R (monitor project costs)	C/R (create for project)	-	C/R (create on behalf of PM)	- (not internal invoices)
Payroll	C/R/W	R (view summary)	C/R/W	-	-	-	-	-
User & Settings	C/R/W (manage users)	-	-	-	-	-	-	-

### (Key

- C=Create, R=Read, W=Write/Update.
- “Own” means records linked to the user’s projects or customer.
- Blank or “-” means no access.)

The above matrix is indicative; actual implementation uses ERPNext’s permission system:

Role permissions by DocType (with conditions like “if Customer field = user’s customer” for client role).

- Document-level restrictions like Permission Query Conditions ensure client only sees their records, and possibly engineer only sees requests if they are assignee or if a field “assigned_to” = their user (this can be done via shared filter or a custom query condition).

### For more complex cases (like PM seeing only their projects), User Permissions in ERPNext can be used

- e.g., assign each PM a User Permission for their Customer or Project, restricting what they see.

UI Access Differences:

Admin and Department Heads likely use the full ERPNext desk interface.

Project Managers and Office Managers also use ERPNext desk heavily (with access to all modules they need).

- Engineers might primarily use the mobile-friendly bot or a simplified interface (maybe an ERPNext portal page or a slim desk page) to avoid the complexity of ERPNext UI.

Clients use a separate portal or bot interface, not the ERPNext desk.

### Two-Factor Authentication

- Admins, Accountants, and perhaps Department Heads are required to use 2FA on login for security.
- Other users may have optional 2FA.
- This is a security policy applied via user settings.

- In summary, the permissions are configured so that each user only sees and does what their role requires, thereby protecting sensitive information (like financials from engineers or other clients) and preventing accidental or unauthorized modifications (for instance, an engineer cannot mark an invoice as paid, and a client cannot see other clients’ projects).
- These controls, combined with audit logs of every important action, create a secure collaborative environment in the ERP.
