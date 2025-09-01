# Monitoring, Analytics & Security (System Oversight and Reporting)

### Figure 7: Monitoring, Analytics & Security BPMN

![Monitoring, Analytics & Security BPMN](../images/monitoring_analytics_security_process.svg)

This final process area covers how the system is monitored and how it provides analytical insights, as well as overarching security measures to keep the system reliable and safe.
- Unlike previous processes, many of these are continuous or event-triggered system functions rather than user-driven workflows.

### System Monitoring & Logs

- Ferum Customizations logs all significant user actions and data changes.
- ERPNext’s versioning feature tracks changes to documents (who changed what and when).
- Additionally, a custom logging module records events like status transitions, approvals, and login attempts with timestamps.
- The Administrator can review audit logs to trace any critical operation (e.g., who deleted a request or who marked an invoice as paid).
- These logs are stored in the database and can be exported or archived.
- The system also aggregates application logs (errors, warnings) which are important for debugging.
- These are periodically archived to Google Drive as well (e.g., monthly compressing and offloading).

- The deployment includes integration with Prometheus for live monitoring.
- A Prometheus agent scrapes metrics exposed by the system – such as request response times, error rates, resource usage, number of open requests, etc.
- – and stores them for visualization.
- The custom backend might expose an HTTP /metrics endpoint providing metrics in Prometheus format.
- Coupled with Grafana (if set up), this allows dashboards like “Number of open service tickets over time” or server CPU/memory graphs.

- For error tracking, Sentry is used.
- The backend and possibly client code are configured with a Sentry DSN, so that any unhandled exception or error is reported to Sentry’s cloud dashboard.
- This proactive alerting allows developers to catch issues (like a failure in the Google Sheets sync, or a bot command error) quickly and fix bugs.

### Analytics & Reporting

- The system generates analytics on operations and finances for decision-makers.
- For example, it computes the average time to close service requests, the on-time completion rate (what percentage of requests are closed before their SLA due date), engineer utilization (how many requests each engineer handles, or hours worked vs capacity), project profitability (invoices vs costs per project), etc..
- Many of these metrics are derived from the transactional data: resolution times from ServiceRequests, financials from Invoices, etc.

- The custom backend includes an Analytics module that can aggregate this data on demand.
- When, say, the General Director wants to see KPIs, they might use the Telegram bot command (e.g., /analytics or specific queries like /project_stats <ProjectID>).
- The backend will query the ERPNext database for relevant data and compute the metrics.
- To optimize performance, the system might cache these analytics results in memory or Redis for a short period (e.g., refresh every few hours), so that repeated requests (like daily KPI checks) are fast.
- The analytics are delivered via the Telegram bot as formatted messages or simple charts.
- For instance, the Director can get a message: “Open Requests: 5 (Avg age 2.3 days); Month’s Revenue: $50k; Overdue Invoices: 2 clients...” and so forth.
- This gives leadership quick insight without needing to run reports in the ERP UI.

### Security Measures

- Security underpins the entire system.
- Authentication to the custom API is done via JWT tokens issued after users log in.
- Additionally, two-factor authentication (2FA) is enforced for users with sensitive access (Admin, accountant, etc.), possibly using OTP codes sent to email or an authenticator app.
- Within ERPNext, user accounts have strong passwords (stored as hashes) and can also use ERPNext’s 2FA by OTP if enabled.

### The system employs role-based authorization at every level

- API endpoints check the user’s role and permissions before allowing access (for example, an engineer trying to call an admin-only endpoint will get a 403 Forbidden).
- In the backend, this is implemented with middleware/guards that verify JWT claims (like role = Admin).
- In ERPNext, role permissions are configured for each DocType: e.g., Clients can only read ServiceRequest and ServiceProject where they are the customer, Engineers can read those where they are assigned, etc.
- Complex permission rules like “Customer can only see their own data” are enforced via permission query conditions in ERPNext, ensuring even if a savvy user tried to access others’ data, the system filters it out at the database query level.

- Sensitive data in the database, such as personal identifiable information (phone numbers, emails of clients) or any confidential notes, are encrypted or hashed when possible.
- For instance, ERPNext by default hashes user passwords.
- The team may also choose to encrypt certain fields (ERPNext has an encryption feature for fields using AES).
- At minimum, all backups are encrypted or stored in an access-controlled location to prevent data leakage.

### Network security

- All web traffic runs through HTTPS with TLS encryption.
- In production, Nginx serves as a reverse proxy in front of ERPNext and the FastAPI service, with proper TLS certificates (e.g., via Certbot).
- This protects against eavesdropping and man-in-the-middle attacks, especially important if users connect via public internet (e.g., a PM using the system from a client site).

- To mitigate brute force or denial-of-service attacks, the system employs rate limiting on the API.
- Using a library like SlowAPI in FastAPI or Nginx’s rate limit module, it limits the number of requests per minute a single IP or user can make to sensitive endpoints.
- This prevents abuse of the authentication endpoint or spammy bot commands from overwhelming the system.

### Backup & Recovery

- A robust backup strategy is part of security (ensuring data is not lost).
- The system performs daily database backups automatically.
- A cron job or scheduler triggers a bench backup (or pg_dump if using PostgreSQL) every night, producing an SQL dump of the ERPNext site and including files (if any not already on Drive).
- These backup files are then uploaded to a secure Google Drive folder dedicated to backups.
- Only the Administrator (or certain IT staff) have access to that folder.
- Backups are encrypted before upload or the Drive itself is restricted to the backup service account (ensuring no unauthorized access to data dumps).
- The system retains a rotation of backups (e.g., last 7 daily backups, plus weekly and monthly snapshots).
- In addition, since most files are already on Drive, they are inherently backed up, but any remaining private files in ERPNext (if used) are included in the backups or separately synced.
- The system also archives log files regularly to Drive for forensic needs.

### A documented Disaster Recovery plan outlines how to restore in case of catastrophic failure

- one would set up a new server, install the same version of the application from GitHub, import the latest SQL dump, and reattach the files directory (or reconnect to the Drive).
- This procedure is tested periodically (the team might perform a test restore on a staging server) to ensure backups are valid.
- With daily backups and cloud storage, the RPO (recovery point objective) is about 24 hours – meaning at most a day of data could be lost in a worst-case scenario, which is acceptable for this project.

- In essence, the Monitoring, Analytics, and Security processes work behind the scenes to keep Ferum Customizations reliable, informative, and safe.
- They ensure the team can trust the system’s data and that management has the insights needed to continually improve operations.
