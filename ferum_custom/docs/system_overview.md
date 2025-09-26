# Ferum Customizations – Technical Specification

System Overview

### Scope & Goals

- Ferum Customizations is a comprehensive IT system built on ERPNext (Frappe v15) to streamline the operations of a fire-safety service company.
- The primary goal is to automate and integrate core workflows – from project and contract management to service requests, work reports, invoicing, HR/payroll, and analytics.
- By consolidating data and processes, the system aims to improve transparency (especially via photo documentation), eliminate manual data entry and duplicated effort, enforce deadlines and quality control for subcontractors, and provide real-time financial metrics like project profitability, accounts receivable aging, and contractor payments.
- Key performance indicators (KPIs) tracked include service request turnaround time, on-time completion rates for work reports, outstanding receivables per project, and staff utilization rates.

### Architecture

- Core: a single ERPNext site with the "Ferum Custom" app (Frappe v15), custom DocTypes (Service Project, Service Request, Service Report, Invoice), server logic and integrations.
- API: Frappe whitelisted methods under `ferum_custom.api.*` with optional JWT (Bearer) auth handled by a `before_request` hook.
- UI: ERPNext Desk for internal users; lightweight portal pages for clients live under `ferum_custom/ferum_custom/www/portal/`.
- Integrations: in-app Python modules for Telegram and Google (Drive/Sheets); external microservices are optional and not required for current functionality.

Technologies: Ferum Customizations leverages a range of technologies and integrations:

### ERP Platform

- ERPNext (Frappe v15), providing base modules (CRM, Projects, HR, etc.) and the framework for custom DocTypes and server scripts.

### Backend

- Implemented in-app on Frappe (Python) via whitelisted methods and hooks.
- Optional: a separate FastAPI service may be added later for extended public APIs, but it is not part of the current repo.

Frontend: ERPNext Desk; optional portal pages (HTML/JS) are provided for client workflows.

### Bots

- Telegram Bot API is used for outbound notifications (simple HTTP calls). Incoming bot command handling, if adopted, would live in a separate service.

### Cloud Services

- Google Drive for report PDF storage and Google Sheets for invoice sync (both via service account credentials stored in `Ferum Custom Settings`).
- Optional: Calendar and other Google APIs can be added later.

### DevOps & Monitoring

- Containerized deployment using Docker Compose, continuous integration with GitHub Actions, monitoring with Prometheus (metrics scraping) and Sentry (error tracking).

### Security

- Optional JWT authentication (Bearer) for API calls; role-based access control via DocType permissions + PQC; TLS via Nginx; configurable per-IP login rate limiting.

### Overall, the architecture is pragmatic

- ERPNext holds the single source of truth. Current integrations run in-process. If future needs arise, external services can be introduced without disrupting the ERP core.
