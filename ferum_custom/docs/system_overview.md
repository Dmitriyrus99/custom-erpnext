# Ferum Customizations – Technical Specification

System Overview

### Scope & Goals

- Ferum Customizations is a comprehensive IT system built on ERPNext (Frappe v15) to streamline the operations of a fire-safety service company.
- The primary goal is to automate and integrate core workflows – from project and contract management to service requests, work reports, invoicing, HR/payroll, and analytics.
- By consolidating data and processes, the system aims to improve transparency (especially via photo documentation), eliminate manual data entry and duplicated effort, enforce deadlines and quality control for subcontractors, and provide real-time financial metrics like project profitability, accounts receivable aging, and contractor payments.
- Key performance indicators (KPIs) tracked include service request turnaround time, on-time completion rates for work reports, outstanding receivables per project, and staff utilization rates.

### Architecture

- The solution uses a modular architecture layered on ERPNext’s server and database, coupled with a custom web application for extended functionalities.
- At its core is an ERPNext site with custom DocTypes for domain-specific records (Service Projects, Service Requests, etc.), running on a Frappe framework with a MariaDB or PostgreSQL database.
- On top of this, a separate backend service (built with FastAPI in Python, or alternatively NestJS in Node) handles API requests, integrates with external services, and powers a React frontend for specialized user interfaces.
- The React frontend provides a modern UI for internal users and possibly clients (portal), while ERPNext’s Desk interface is still used for core data entry and internal workflows.

Technologies: Ferum Customizations leverages a range of technologies and integrations:

### ERP Platform

- ERPNext (Frappe v15), providing base modules (CRM, Projects, HR, etc.) and the framework for custom DocTypes and server scripts.

### Backend

- Python 3.10+ with FastAPI (including Pydantic models for validation).
- This service exposes RESTful APIs and handles business logic outside ERPNext (e.g.
- bot interactions, Google API calls).

Frontend: React (JavaScript/TypeScript) for any custom web UI components or client portal.

### Bots

- Telegram (via Aiogram Python library) and WhatsApp bot integrations for notifications and user commands (engineers and clients can interact with the system through messaging apps).

### Cloud Services

- Google Workspace integration – Google Sheets for data synchronization (e.g.
- tracking invoices) and Google Drive for file storage.
- Also optional Google Calendar integration for scheduling.

### DevOps & Monitoring

- Containerized deployment using Docker Compose, continuous integration with GitHub Actions, monitoring with Prometheus (metrics scraping) and Sentry (error tracking).

### Security

- JWT-based authentication with 2FA for the custom API, role-based access controls enforced both in ERPNext and the backend, TLS (HTTPS) via Nginx reverse proxy, and request rate limiting (using tools like SlowAPI).

### Overall, the architecture is hybrid

- a monolithic ERP for core data and a microservice-like web app for integrations and interfaces.
- The components communicate primarily through REST API calls (the custom backend calling ERPNext’s API or direct database access via Frappe client) and webhook integrations (for bots and Google services).
- The diagram below illustrates the high-level architecture, with ERPNext at the center, the custom FastAPI backend and React UI on the side, and external services (Telegram/WhatsApp, Google APIs) interacting through defined interfaces (diagram not shown).
- This architecture ensures that while ERPNext holds the single source of truth for business records, the system is extensible and can evolve into microservices if needed (e.g.
- spinning off analytics into a separate service).
