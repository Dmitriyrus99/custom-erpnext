# Glossary and Appendix

Glossary of Terms & Acronyms:

### ERPNext

- An open-source Enterprise Resource Planning platform built on the Frappe framework.
- In this context, it is the core system hosting our custom DocTypes and standard modules (Customer, Employee, etc.).

### Frappe Framework

- The underlying web framework for ERPNext (Python + MariaDB/Postgres + Redis stack) which allows rapid development of DocTypes, forms, and APIs.

### DocType

- In Frappe/ERPNext, a DocType is essentially a data model (like a table) plus form definition.
- We created custom DocTypes such as ServiceProject, ServiceRequest, etc., each with fields and logic.

ServiceProject: A maintenance contract or project record, grouping service requests under a particular client contract.

### ServiceObject

- A piece of equipment or a site location that is serviced.
- E.g., a fire alarm control panel, a sprinkler system, etc., belonging to a customer.

### ProjectObjectItem

- A child record linking a ServiceObject to a ServiceProject, used to list all objects under a contract.

### ServiceRequest

- A ticket representing a maintenance issue or service call.
- Contains issue details, status, etc., similar to a work order.

### ServiceReport

- Also called an Act of Completed Work, this is the report/document that details what work was done for a service request.
- Usually corresponds 1:1 with a completed ServiceRequest.

Work Item (ServiceReportWorkItem): An entry in a ServiceReport listing a specific task or part, quantity, and cost.

### Attachment (CustomAttachment)

- A file (image, PDF, etc.) uploaded to the system and linked to other records (requests, reports, invoices).
- We unified attachments under this doctype for easier management.

### Invoice

- A billing record.
- In this system, invoices can represent outgoing invoices to clients or incoming bills from subcontractors, distinguished by a field like counterparty type.

PayrollEntryCustom: Custom payroll document aggregating payroll info for employees, including net pay calculations.

### KPI

- Key Performance Indicator.
- Metrics used to evaluate success: e.g.
- average request turnaround time, on-time completion rate, etc..

### SLA

- Service Level Agreement.
- A defined expected time frame for response or resolution of a service request (e.g., 4 hours response for emergencies).

### Telegram Bot

- A chat-bot on Telegram platform configured for this system to allow notifications and user commands (for engineers and clients).

### WhatsApp Integration

- Similar to Telegram bot but on WhatsApp for potentially reaching users there.
- (Likely via WhatsApp Business API.)

### Google Workspace

- Suite of Google applications.
- Here specifically:

Google Sheets: Used for the invoice tracker spreadsheet.

### Google Drive

- Cloud file storage where we store attachments (photos, scanned documents) instead of on the ERPNext server.

(Google Calendar): Potential use for scheduling events for requests (not fully implemented yet).

### Prometheus

- An open-source monitoring system.
- Scrapes metrics from our app (e.g., number of open requests, response times) for analysis and alerting.

### Sentry

- A cloud-based error monitoring service.
- Our backend sends exception traces to Sentry so developers can fix issues proactively.

### JWT (JSON Web Token)

- A token format for API authentication.
- Encodes user identity and is signed to prevent tampering.
- Used for our custom API auth.

### 2FA (Two-Factor Authentication)

- An extra layer of login security requiring a secondary code (often via authenticator app or SMS/email).

### CI/CD

- Continuous Integration / Continuous Deployment.
- CI refers to automated build and test (on GitHub Actions) for every code change.
- CD refers to automated or easy deployment of those changes to staging/production.

### Docker & Docker Compose

- Containerization technology.
- We use Docker images for the app, DB, etc., and Compose to orchestrate them in development and production for consistent environments.

### Bench

- The command-line tool for Frappe/ERPNext that manages sites, apps, migrations, etc.
- (We use it inside containers for tasks like migration, site creation).

### Site

- In ERPNext, a site is an instance (database + files) of ERPNext.
- We have one site (likely named something like erp.ferumrus.ru) which has our custom app installed.

### Hook

- A custom function that runs on certain events (e.g., validate, on_submit) of a DocType.
- We implemented hooks for validations and automation (like ServiceProject.validate).

### Patch

- A script to migrate or fix data schema when the app is updated.
- Listed in patches.txt, executed via bench migrate to apply database changes.

### Public/Private Files

- In ERPNext, files can be public (accessible via URL if you know it) or private (require permission and go through auth).
- We likely treat attachments as private, especially since accessed via our API or after login.

### Contractor vs Subcontractor

- In our context, subcontractor refers to an external service provider our company hires to do work.
- Sometimes just called contractor.
- We treat their invoices as a type of Invoice in system (counterparty not a Customer but a vendor).

### Act (of work performed)

- A term used (especially in Russian context "Акт") for a document that both service provider and client sign after work is done, confirming completion.
- Essentially what we call ServiceReport when signed.

Appendix: Document Templates and Workflows

(This appendix can list any standard templates or workflows if they exist outside the above narrative.)

### Service Report Print Format

- A standardized PDF layout including company header, client name, reference to ServiceRequest, table of work items, total amount, space for client and engineer signatures.
- This template is used when printing or emailing a ServiceReport.

### Invoice Template

- If using a custom format for invoices (the app might just use the PDF provided by subcontractor for vendor bills, and for client bills might have an HTML template).
- Ensures company details, tax info, bank details are present.

### Welcome Email Template

- A pre-written email that goes to new project clients, including login info to portal perhaps, contact points, and summary of contract scope.

Notification Matrix: (Could be a table showing which events trigger notifications to whom, as partially described.)

E.g., New Request: notify Assigned Engineer (bot + email), PM (email), Client (acknowledgment if entered by staff).

Request status to Completed: notify client (email "Your issue resolved, please verify").

Invoice uploaded: notify Admin (bot/email).

And so on.

Business Process Diagrams:

- [Figure 1: Project & Contract Management BPMN](images/project_contract_management_process.svg)
- [Figure 2: Service Request Management BPMN](images/service_request_management_process.svg)
- [Figure 3: Work Reporting BPMN](images/work_reporting_process.svg)
- [Figure 4: Invoicing & Payments BPMN](images/invoicing_payments_process.svg)
- [Figure 5: HR & Payroll BPMN](images/hr_payroll_management_process.svg)
- [Figure 6: Document & Attachment Management BPMN](images/document_attachment_management_process.svg)
- [Figure 7: Monitoring, Analytics & Security BPMN](images/monitoring_analytics_security_process.svg)

These diagrams illustrate step-by-step flows and decision gateways for each process (for reference during training or onboarding).

Standard Operating Procedures: Some processes might have slight manual steps beyond the system:

- E.g., after closing a request, the PM is supposed to call the client to ensure satisfaction within 1 day.
- (If such a thing, not enforced by system but could be note in SOP).

- Or monthly, Office Manager should check that all open requests are followed up.
- They could use an ERPNext report "Open Requests > 7 days" to do this.

Change Log: A running list of changes per release (for project management transparency).

Attachment: Roles & Permissions Matrix: (If needed as a table to recap, which we did above in text.)

- By defining these terms and providing supporting details, we ensure all stakeholders (developers, users, etc.) share a common understanding of the system.
- This completes the technical specification, offering a comprehensive blueprint for implementation and future reference.
- All requirements from the business process model have been traced into this design, providing a solid foundation for development and deployment of Ferum Customizations.
