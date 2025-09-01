# Integrations

- Ferum Customizations is designed to work seamlessly with several external systems and tools to enhance its functionality.
- Key integrations include Google Workspace (for spreadsheets and drive storage), messaging platforms (Telegram/WhatsApp bots), and monitoring tools (Prometheus and Sentry).
- This section describes each integration, how data flows, and any configuration or API usage details.

### Google Sheets Integration (Data Sync for Invoices)

- The system integrates with Google Sheets to track and summarize financial data (primarily subcontractor and client invoices) in real-time.
- A specific Google Sheet (let’s call it "Invoice Tracker") is set up with predefined columns and formulas.
- Whenever a new Invoice record is created or updated in ERPNext, the integration uses the Google Sheets API to add or update a row in this spreadsheet.
- For example, columns might include: Project Name, Counterparty (Client or Subcontractor), Month, Amount, Entered By, Status, Paid Date.
- The system authenticates to Google via a service account or API key stored securely (in environment variables not in code).
- On invoice creation, the backend sends a request to Google’s API endpoints (which typically use a JSON payload to append rows or edit ranges).

Some logic is implemented in the sheet itself:

- The sheet has formulas to auto-calculate totals per project and per month, perhaps using pivot tables or sumif formulas.
- This gives management a quick aggregate view without running a report in ERPNext.

- Conditional formatting is used (or an Apps Script) to highlight rows where the person who entered the invoice is not the assigned PM for that project.
- The system can facilitate this by including the PM’s name and the entry user’s name in the row data, and a cell formula can compare them and highlight if mismatch (with exceptions for certain projects like overhead categories as noted).

- Because multiple users might view the sheet, it is shared with the relevant staff (Admin, accounting, maybe PMs in view-only).

- The integration is one-way (ERPNext -> Sheets) for data entry.
- Updates on sheet (like marking something paid) ideally should flow back or be reflected in ERPNext.
- Currently, marking an invoice as paid is done in ERPNext by Admin, and optionally the integration could update a "Paid" column in the sheet (either immediately or the sheet could use VLOOKUP via an exported list of paid invoices).
- For simplicity, it might remain one-way: staff mark paid on both ERPNext and manually tick in sheet or the sheet could be purely a reporting tool rather than the source of truth.

- From a technical perspective, the integration likely uses Google’s REST API with a library (like Google API Python client) to append rows.
- It might batch updates if many invoices are created together.
- Error handling is important: if Google API is down or rate-limited, the system should queue the update to retry later and log it.
- A log of last sync time or any failures might be kept (so Admin can see if an invoice didn’t make it to the sheet).
- This ensures data consistency between systems.

### Google Drive Integration (Document Storage)

- All files uploaded into the system (photos, reports, scans, etc.) are offloaded to Google Drive to leverage its storage and sharing capabilities.
- The integration strategy:

- A dedicated Google Drive folder (or a set of folders) is used as the root for Ferum files.
- For instance, a main folder "FerumFiles" with subfolders for Projects, Service Requests, or just a single bucket if decided so.

- When a user attaches a file in ERPNext (or via the API), the file is first saved to ERPNext (either temporarily or as a File doc).
- Then, in the background, an upload to Drive is initiated.
- The system uses the Drive API (with the credentials of a service account that has access to the designated Drive folder).
- It uploads the file content and metadata (like name).
- If using subfolders by project, it will ensure the folder exists (creating it if not on first use) – e.g., a folder named after the project or customer.
- If not using subfolders, it may prefix file names with some project or request ID to logically group them.

- The CustomAttachment record in ERPNext stores the returned Drive file ID or a shareable link.
- Possibly both: storing the ID for API deletion and the web link for quick access.
- Access to these files is restricted – ideally, the Drive folder is not public.
- If users need to view/download a file through ERPNext, the system could fetch it via API and stream, or the link could be a Drive "anyone with link can view" if the business is okay with that.
- More securely, the system might act as proxy: when a user with permission clicks an attachment, it uses the stored file ID to fetch from Drive with the service account and then serves it to the user (ensuring only authorized users get it).

### Deletion

- When a file attachment is deleted in ERPNext, the system calls Drive API to remove that file from Drive.
- If a file is replaced or updated, it might either upload a new file and delete old or update in place if content changes (likely treat as new file).

### Bulk upload

- In cases where many photos are attached offline, perhaps a script can also be used to sync them.
- But normally each attach triggers its own upload.

- The advantage is that Drive automatically provides backup of files (Google’s infrastructure).
- But to be safe, they might still backup certain critical docs elsewhere (though Drive is reliable).

### Telegram Bot Integration

- The Telegram Bot serves as both an alerting mechanism and an input method for the system.
- Implementation details:

- The bot is developed using Aiogram (a Python async framework for Telegram bots) as indicated in the tech stack.
- It runs as part of the custom backend service.
- A bot token from BotFather is configured (TELEGRAM_BOT_TOKEN in .env).

When the bot is launched, it connects to Telegram’s servers and listens for commands or messages.

### Alerts (Outbound)

- The system uses the bot to send messages to users or group chats for certain events.
- For example:

### New Service Request

- send a message to a Telegram group “Service Team” with summary (“New Request #123 from Client X: [issue]”).
- Or directly message the assigned engineer if assignment is immediate.

Emergency Request: send high-priority alert to perhaps a pinned message or special group of on-call engineers.

New Invoice: send a message to Admin (“Invoice #INV-0005 uploaded by PM John for Project ACME, amount $5000.”).

### Report submitted

- notify admin/PM (“Engineer Mark submitted Service Report SR-00010 for Request #123.
- Please review.”).

- These are done by the backend when those events happen, using the Telegram API (Aiogram provides methods like bot.send_message(chat_id, text)).
- The challenge is knowing chat IDs: for individual notifications, the user’s Telegram ID must be known (the system might store a mapping in a doctype or a simple database linking ERPNext user to Telegram user ID).
- This mapping likely is set up during initial bot usage – e.g., the user sends a command like /register and the bot asks them to authenticate (maybe provide an API token or short code from their ERPNext profile) to link accounts.

- For group notifications (like a “New request” to a team channel), the chat ID of that group is configured in settings (maybe an env var or DB record).

Commands (Inbound): The bot supports various commands as earlier noted:

### Authentication

- possibly /login or a /start that initiates linking.
- But since the environment is internal, they might pre-provision or manually link.

- /new_request – likely for clients.
- The bot will collect needed info (maybe through a guided conversation: "Which project or object is this for?" "Describe the issue:" etc.).
- Then it calls the API to create the request.

- /my_requests – for engineers to retrieve a summary of their open tasks.
- The bot calls GET /requests?assigned_to=me and formats a list in the chat.

- /request_status <ID> or clicking a button – to get status of a given request, though an engineer likely knows their tasks; a client might query status by ID if they have multiple.

- /set_status <ID> <Status> – for engineers or PMs to update a request’s status (start work or complete).
- The bot verifies the command format and calls the API.
- The response is then relayed (success or error).

- /upload_photo <ID> – the bot will prompt user to send a photo, then attach it to the given request.
- Behind scenes, the bot receives the photo file, possibly resizes if needed, then calls the attachments API as described.
- It might confirm "Photo attached."

/help – lists available commands and their syntax.

### Perhaps specialized ones like /analytics for Admin to get KPI summary (the bot then calls an analytics routine to gather key metrics and replies with something like “Open Requests

- 5, Avg Close Time: 2d, This Month Revenue: $X”).

### WhatsApp Integration

- The specification mentions WhatsApp as well, likely to ensure communication on that channel as some clients or engineers might prefer it.
- WhatsApp doesn’t allow bots as freely as Telegram.
- Options:

- Use Twilio WhatsApp API or another provider to send/receive WhatsApp messages.
- This requires a WhatsApp Business number and using their cloud API.

### Possibly they plan a simpler route

- like using email-to-WhatsApp gateways or manual handling.
- More likely they will integrate properly via Twilio or WhatsApp Cloud API with a webhook to the backend.

### Implementation could mirror Telegram

- define certain keywords or commands via WhatsApp messages.
- E.g., a client could send "STATUS <request_id>" and the system replies with status.
- Or simply allow free text creation of requests: e.g., client WhatsApps "Having an issue at site X: the alarm is beeping", the system might interpret that as a new request (this requires natural language or at least a known format).

- Given complexity, they might limit WhatsApp integration to notifications only in phase 1 (e.g., client gets a WhatsApp message "Your request has been completed").
- This is easier: using Twilio API to send outbound template messages.

- In any case, the integration will involve the backend hitting an external API similar to how email is done or receiving webhook calls for incoming messages.
- It’s an area likely to be expanded as needed.

### Prometheus & Metrics Integration

- For system monitoring, a Prometheus server can scrape metrics from the application.
- Typically:

- The backend (FastAPI) includes a middleware or endpoint (like /metrics) that outputs metrics in Prometheus format (text with lines like requests_total{endpoint="/requests"} 1234).
- Libraries like prometheus-client for Python can be used to track counters, histograms, etc.
- They can instrument web requests (to measure request count, latency per endpoint), background job results, etc.

- Additionally, ERPNext itself can expose some metrics (though not by default; could be added via a plugin or just rely on backend metrics).

- Prometheus is configured (outside the app) to pull these metrics periodically.
- It's likely running in the same server or accessible network.
- The deployment would include a Prometheus container or service scraping the ferum_customs backend and maybe database or OS metrics.

- With metrics, they can set up alerts (for example, if error rate > X or if backup hasn’t run, etc., but that might be later).

### Visualization

- possibly a Grafana dashboard to show technical metrics and maybe business metrics like open requests count (the backend can expose a gauge for current open requests count, updated periodically by a scheduled job that queries ERPNext).

- These metrics ensure performance and health monitoring.
- For instance, memory usage, number of active users, etc., could also be exported.

### Sentry Integration

- The system integrates with Sentry for error tracking.
- Implementation:

- The backend has the Sentry SDK configured with a DSN (likely as environment variable).
- It’s initialized on app startup to catch unhandled exceptions and send them to Sentry.

Additionally, client-side (if any custom React frontend) could also have Sentry for front-end errors.

- ERPNext server scripts might not directly integrate with Sentry, but major failures in hooks could be caught by a try-except that logs to Sentry via frappe.log_error or directly calling Sentry SDK if accessible.
- Possibly easier is to rely on the backend: if ERPNext code fails quietly, it might not get to Sentry unless forwarded.
- However, the backend covers most integration points where things could fail (Google API calls, bot actions, etc.), so those are instrumented.

- Sentry helps in identifying issues like an exception in the Google Sheets sync or a bot command crash due to unexpected input.
- Developers can then get notifications and debug with stack traces from Sentry.

Email Integration: Although not in the bullet list, email is implicitly integrated:

- ERPNext’s Email Queue is used for sending out emails like notifications and sending documents to clients.
- The system likely has an SMTP configured (maybe Gmail SMTP or a company mail server).

- Template notifications (like New Request emails) are configured either as ERPNext Notification documents or in Python using frappe.sendmail.
- For example, on new request, send an email to engineer’s corporate email with a template "New Request assigned: [details]".
- Or on request completed, send to client "Work completed, thank you".

These emails can include attachments (like PDFs of reports) as needed.

### The system also might receive emails

- a catch-all that converts to ServiceRequest (ERPNext has a feature for Issue tracking via email).
- That could be configured if, say, they want an email to support@company to generate a ServiceRequest.
- Not explicitly stated, but it’s a possible extension.

### Calendar Integration (potential)

- The spec mentioned as a potential idea integrating with Google Calendar for scheduling visits.
- If implemented:

- When a ServiceRequest gets scheduled (perhaps they set planned start/end times in the request), the system could create a Google Calendar event on a shared calendar (like "Maintenance Schedule") for that time, with the engineer as attendee.

- Use Google Calendar API to create events.
- Or simpler, an iCal file could be generated and emailed.

This is a nice-to-have and might be tackled after core features.

External System (1C) Integration (future consideration):

- They mentioned manual steps for adding new client in KUB-24 or 1C.
- In the future, they might integrate with those enterprise systems.
- This could involve exporting data (like clients or invoices) in a certain format 1C can import.
- For example, generating a CSV or using 1C’s web services if available.

- At present, it's out-of-scope, but the system is designed to allow such integration by having clean data that can be exported easily.

- All integration keys and secrets (Google API credentials, Bot token, Sentry DSN) are stored securely in environment variables or a config file not in code repo (the DEPLOY.md instructions to copy .env likely include these).

Security and Rate limiting for Integrations:

- The Google APIs have rate limits; the system is low volume so unlikely to hit them.
- But if a burst of 100 invoice creations happened, the integration should ideally batch or have a slight delay to avoid hitting Google’s quota.

- For Telegram, ensure not to send messages too fast to avoid bot being flagged (also unlikely an issue with moderate usage).

### The bot interactions themselves are secured by design

- a random person can’t control it because they need to link their account.
- The group chats used for notifications should be private/invite-only.

- The WhatsApp integration, if open to inbound from unknown numbers, needs to verify the sender (maybe using the phone number to look up a Customer record).

Prometheus endpoint is not exposed publicly (only accessible internally).

- Sentry data is encrypted over TLS and doesn’t include PII by filtering (the devs can configure Sentry SDK to not send sensitive fields).

- In summary, these integrations extend the platform’s capabilities beyond the core ERP.
- They ensure that:

Data flows into management-friendly tools like Google Sheets for financial oversight.

Files are safely stored and accessible via Drive.

Real-time communication is enabled through Telegram/WhatsApp, bridging field operations and system data.

- The technical health of the system is monitored via Prometheus, and errors are caught via Sentry so the team can respond quickly to any issues in the integrations or core logic.
