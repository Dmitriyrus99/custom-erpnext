# Security Architecture

- Security has been woven into every part of Ferum Customizations – from data access controls to network communication and backup practices.
- This section summarizes the security measures under different aspects: access control, data protection (encryption), backup and recovery, audit trails, and web security (HTTPS, rate limiting).

### Role-Based Access Control (RBAC)

- As detailed in the roles and permissions section, all system access is governed by roles and finely-grained permissions.
- In ERPNext, each DocType has permission rules for read/write/create for each role.
- Additionally, record-level restrictions ensure users only see records they should (clients see only their records, etc.).
- This is implemented via ERPNext’s built-in mechanisms:

### Permission Query Conditions

- For example, on ServiceRequest, a condition like customer = session.user.customer is applied for the Client role to filter data.

### User Permissions

- For Project Managers, a user permission can link them to specific project or customer records, thereby restricting the view to those projects.

### Sharing

- If an exception is needed (like temporarily giving an engineer access to another engineer’s ticket), sharing can be done by admin for that document.

- The custom API layer also double-checks authorizations on each endpoint call, as described.
- Thus even if someone tried to craft an API call outside their privileges, they’d get denied (defense in depth).

### User account management

- Admins can create users and assign roles.
- Default strong password policies are enforced (minimum length, etc.).
- All default ERPNext admin accounts are secured (the deployment steps involve setting strong admin passwords).
- Dormant accounts can be disabled by Admins.

### Two-Factor Authentication

- Sensitive accounts (Admin, Accountant, possibly PM and any user with broad access) are required to use 2FA on login.
- ERPNext supports time-based OTP 2FA; this is enabled in site config or user settings.
- Additionally, the custom JWT auth process also supports 2FA: the token endpoint expects an OTP for those users.
- This greatly reduces risk of credential compromise leading to data breach.

Data Encryption:

### At-Rest Encryption

- The system uses encryption for certain sensitive fields.
- For example, if storing any credentials or API keys in the database (like integration tokens), those are encrypted using Frappe’s built-in encryption (which uses AES encryption with a site-specific key).
- Also, fields like customer contact email or phone could be encrypted if privacy is a concern (so that even if someone accessed DB dumps, they couldn’t easily extract client PII).
- In practice, ERPNext doesn’t encrypt standard contact fields, but the mention suggests they are aware of data sensitivity.
- At least, the database is on a secure server; encryption at rest might rely on disk encryption at the VM/OS level or database-level encryption for extremely sensitive info.

### In-Transit Encryption

- All external communications are over HTTPS or secure channels.
- The web interface is served via HTTPS, with Nginx configured with a valid TLS certificate (Let’s Encrypt via Certbot as per deployment steps).
- This protects against eavesdropping, especially since users may access the system from external networks.

- The Telegram and WhatsApp communications are end-to-end encrypted by those platforms.
- The integration with them uses their encrypted APIs.

### Backup Encryption

- Database backups are sensitive (they contain all data).
- If they are stored on Google Drive, at minimum the Drive is secure (only accessible by authorized accounts).
- For extra security, backups could be PGP or AES encrypted before upload.
- The specification suggests either encrypting backup files or ensuring the Drive access is restricted.
- We plan to generate backups as .tgz or .sql files and optionally encrypt them with a symmetric key before uploading.
- The key would be stored off-site (with the admin).

- Passwords are hashed using bcrypt (ERPNext’s default) and never stored in plaintext.
- The system possibly also salts and hashes certain other fields if needed.

Audit Logs and Monitoring:

- ERPNext keeps a Version log of changes to documents.
- Every edit, submit, cancel event on a DocType can create a version record noting the user and changed fields.
- This is enabled for key DocTypes (ServiceRequest, ServiceReport, Invoice, etc.).
- Admins can review these via the Version list or the document’s Timeline in UI.

- The system extends logging by writing critical events to a custom log (maybe a text-based system log or an Audit Trail doctype).
- For instance, whenever an Invoice status changes or a user logs in, it could log “User X changed Invoice Y status to Paid at 2025-08-11 10:00”.

- The Prometheus metrics include things like number of login attempts, number of failed auths, etc.
- If unusual patterns (possible intrusion attempt) are detected (like repeated 401 responses), an alert can be raised via Prometheus Alertmanager to admins.

- Sentry logs all exceptions – which not only helps debugging but also acts as an audit of system errors, possibly highlighting suspicious events (like if an API endpoint was called with an unexpected payload by an attacker, causing an error that shows up in Sentry).

Rate Limiting and DoS Protection:

- The custom FastAPI layer likely uses slowapi or Starlette middleware to enforce rate limits.
- For example, limit 5 login attempts per 15 minutes per IP to prevent brute force.
- Limit general API calls to, say, 100 per minute per user/IP which is plenty for normal use but blocks flooding.

Nginx is configured with basic rate limiting as well (e.g., limiting new connections).

- The system size is small (few dozen users), so real DoS might be more external.
- Nginx + fail2ban could block IPs that hammer endpoints.

- Bot usage commands are inherently limited by user input, but if a bot were compromised or spammed, the backend also has global limits to not let it overload the system with requests.

Network Security:

- The application is containerized.
- Only necessary ports are exposed (443 for web, maybe 80 for redirect to 443).
- The database and other internal services are not accessible from outside (Docker Compose config ensures DB only accessible to the app).

- Nginx sits in front of the ERPNext gunicorn and the FastAPI app, and can restrict protocols/ciphers to secure ones, and enforce HTTP security headers.

The server environment likely has firewall rules (only allow traffic to web ports).

- The Telegram/WhatsApp and Google API calls are outgoing initiated from the app, which is fine.
- If any of those require inbound webhooks (Telegram can push updates via webhook or polling; they might use polling to avoid exposing a webhook endpoint; WhatsApp cloud might do webhooks though), in case of webhooks, a specific endpoint would be opened and should have a verification token to ensure authenticity.

### A separate consideration

- the environment might be multi-tenant (ERPNext bench could host multiple sites, but here it’s probably single-tenant for this company).
- The site is named (like erp.ferumrus.ru perhaps, as some backup path in code review indicates).

The database (PostgreSQL if used) can optionally encrypt connections as well, but since it’s local, not crucial.

Backup Policy & Disaster Recovery:

### Frequency

- Full database backups are done daily (likely at off-peak hours, e.g.
- 2 AM), with perhaps additional weekly backups stored for longer.

### Retention

- At least 7 daily backups and some weekly or monthly snapshots are kept.
- Older ones beyond that are pruned to save space.

### Storage

- Backups are uploaded to Google Drive (or potentially another cloud storage if chosen) immediately after creation.
- They might also keep a local copy for a short time, but off-site storage protects against server loss.

### Integrity

- Each backup job is logged; if a backup fails, the system alerts admin (perhaps via Sentry or email).
- The admin should check Drive to ensure backups appear.

Restoration procedure: Documented in backup.md:

1. Get the same version of code (from GitHub commit tagged).

- 2.
- Restore the database from SQL dump.

- 3.
- Restore the files directory (if not using Drive exclusively, any private files stored).

- 4.
- Reinstall the app on a fresh site and import data.
- Then verify data integrity.

- Periodic test restores are recommended – e.g., spin up a staging environment and do a trial restore from a backup to ensure the process works and backups are valid.

- Also, key config like .env and encryption keys should be backed up (but carefully, perhaps in a secure vault, since losing the encryption key would render encrypted fields unrecoverable).

High-Level Security Practices:

- Use of production-grade infrastructure (supervisor, Nginx) as per bench setup ensures processes run with correct privileges (frappe user, etc., not root).

Operating system is kept updated (security patches).

- The Docker images likely come with up-to-date OS and only necessary packages (the CI might build images with each release).

- Secrets (like DB password, API tokens) are not exposed in code or logs.
- Only admins have access to the .env and server.

### The system monitors itself

- if any suspicious behavior (like multiple failed logins) occurs, an admin can notice via logs or metrics.
- Possibly, integrate Fail2Ban for SSH or web if necessary.

- With these layers – application security, network security, data security, and operational security (backups and monitoring) – the Ferum system is well-protected against both external threats and internal misuse.
- No system is 100% risk-free, but the above measures follow best practices for an ERP handling moderately sensitive data (financials and personal info).
- The team will continue to review security, especially as new integrations (like WhatsApp or if a public client portal is opened broadly) are added, conducting at least basic penetration testing or using ERPNext’s built-in security advisories (like ensuring no user has weak password, etc.).
