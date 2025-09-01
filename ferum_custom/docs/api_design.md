# API Design

- The Ferum Customizations platform exposes a set of RESTful APIs to allow integration with external clients such as the Telegram/WhatsApp bots and any custom React frontends or mobile apps.
- All API calls are secured via authentication and role-based authorization.
- Below is an outline of the API endpoints, their purpose, and design considerations including payloads and security.

### Authentication & Authorization

- The API uses JWT (JSON Web Tokens) for auth.
- Users (or bots) must obtain a token (for instance, by providing username/password to an auth endpoint, or in the case of the bot, using a pre-shared API token mapped to an internal user).
- All subsequent calls require the JWT in the header (e.g., Authorization: Bearer <token>).
- The JWT payload encodes the user ID and roles, and is verified by the backend on each request.
- For an extra layer, two-factor auth is enforced during token issuance for users who have 2FA enabled: e.g., the user must also supply a one-time code (from email or app) to get the token.
- Tokens have a short lifespan (perhaps 1 hour) and can be refreshed with a refresh token to reduce login frequency.
- The backend verifies the user’s roles and permissions on each request and can further restrict data returned based on user (e.g., a client’s JWT will only allow access to their own project data).

### Error Handling & Responses

- The API returns standard HTTP status codes.
- 200 for success (with JSON payload), 4xx for client errors (401 for unauthorized, 403 for forbidden actions, 400 for validation errors detailing what was wrong), and 500 for server errors.
- The payload typically contains a JSON object; for example, for a GET list request, it might be {"data": [ ...items...
- ]}; for a single get, {"data": { ...item...
- }}; for errors, something like {"error": "Description of error"}.

Now, the major endpoints by module:

Projects API:

- GET /projects – Retrieves a list of service projects.
- Supports filters such as ?customer_id=XYZ, ?status=Active.
- Only accessible by roles that can view projects (Admins see all; PMs see their projects; Clients see their own) – the backend will filter based on the JWT’s user roles and possibly append a filter for client user (customer=that client) if client role.
- Response includes project fields and maybe a summary (count of open requests, etc.
- if needed).

- GET /projects/{id} – Gets details of one project, including associated ServiceObjects and possibly a summary of requests and invoices.
- Authorization: the requesting user must have access to that project.

- POST /projects – Creates a new project.
- Expects JSON payload with project details (customer, dates, name, etc., and a list of service object IDs to link or data to create new service objects).
- Only Project Managers or Admins can call this.
- The backend will perform the same validation as ERPNext would (perhaps by actually calling Frappe API to insert the document, which triggers the hooks that ensure uniqueness, etc.).
- If successful, returns the created project data or ID.

- PUT /projects/{id} – Updates project info (e.g., extend end date or change status).
- Allowed for PM of that project or Admin.
- Could also be used to add/remove ServiceObjects (though that might be easier via separate endpoints).

- Possibly POST /projects/{id}/objects to attach a new ServiceObject to a project, or this might be done through a normal update with child table.

Service Objects API: (not heavily used externally, but for completeness)

GET /objects – list of service objects (filterable by customer or project).

- POST /objects – to create a new ServiceObject (the portal might allow a client to register a new piece of equipment).
- Would require at least Admin/PM or a Client could create one that is auto-linked to their customer (client user input).
- The system might restrict whether clients can create objects; if not, they would call the office to do it.

Most object management is internal via UI, so API usage is minimal here.

Service Requests API:

- GET /requests – List service requests.
- Supports filters: by status, by project, by assigned engineer (e.g.
- ?assigned_to=user123), or by customer (implicitly via auth).
- For an engineer, calling GET /requests?status=Open might return only their open requests if we enforce that in query.
- Alternatively, an engineer’s client would be different – better to rely on auth: For Engineer role, the backend might by default filter to assigned_to = that engineer unless an Admin making the call.
- For a client, it filters to requests where customer = client’s customer id.
- Response returns basic info for each request (ID, subject, status, maybe priority and dates).

- GET /requests/{id} – Get full details of a specific request, including all fields, and potentially embed the child table of attachments and link to ServiceReport if exists.
- Only accessible if user has rights to that request.

- POST /requests – Create a new service request (used by clients via portal/bot, or by any integration).
- The payload should include either a service_object or a free-form address if no object, a description, and perhaps a type/priority.
- If a client calls this, the backend will automatically link their Customer and possibly find the relevant project (if a service_object is given, it knows the project; if not, maybe try to find an active project for that customer; if still none, it could create as a standalone request not under a contract).
- On success, this endpoint triggers the standard notifications (email/bot messages) as part of the creation logic.
- Returns the created request ID and data.

- PUT /requests/{id} – Update the request’s details.
- Limited usage externally; could allow editing description or reassigning engineer (though normally assignment is done internally).

- PUT /requests/{id}/status – Change the status of a request.
- This is safer than general update as it can enforce allowed transitions.
- The payload might be {"status": "In Progress"} or {"action": "start"} etc.
- The backend will check the current status and the user’s role: e.g., an engineer can move Open -> In Progress -> Completed, but cannot Close, whereas an Admin can move any status including to Closed or Cancelled.
- It also checks for the ServiceReport existence if setting to Completed/Closed.
- If violation, it returns 400 with error like "Service report required".
- On success, it updates and triggers any side effects (if marking Completed and no end time, set it; if Closed, maybe send satisfaction survey to client, etc.
- – last part optional).

Attachments via API: For the bot to upload photos, likely an endpoint:

- POST /requests/{id}/attachments – to attach a file.
- This would accept a multipart form-data with file upload (or an encoded file) and a description field.
- It would then create the CustomAttachment and link it.
- Response might just confirm upload success.
- Alternatively, they could do in two steps: first upload file to an upload endpoint that returns an attachment ID or URL, then call another endpoint to link it.
- But for simplicity, one call is better from bot.

Service Reports API:

- GET /reports – List of ServiceReports.
- Filter by project or date, etc..
- Likely only Admin/PM would use this (e.g., list all reports in last month).
- Engineers or clients might not call this directly except via a specific scenario.

- GET /reports/{id} – Get detailed ServiceReport.
- Returns the report fields, and possibly an array of work items and attachments.
- Clients could use this to view the act of work done (if given access).
- It might be restricted to internal roles by default, with an exception that if the ServiceReport’s project’s customer == the client’s customer, the client role can read it (if they want clients to see the final report).

- POST /reports – Create a new ServiceReport.
- This could be used by a mobile interface if an engineer in the field wants to create a quick draft report.
- Payload might include: service_request ID, list of work items (which could be simplified as a text summary or a small list for minor jobs), and any immediate attachments.
- Given complexity, likely this API is rarely used (engineers might prefer to just mark request Completed and let office complete the formal report).
- But it’s available to integrate the bot if needed.

- PUT /reports/{id} – Possibly allow updating/adding attachments (like if a signed scan comes in later, an endpoint to attach it, or mark a field like signed_by_client = true).

Invoices API:

- GET /invoices – List invoices.
- Likely only Admin and accountants use this.
- Filter by status or project (e.g., all unpaid invoices, or all invoices for project X).

GET /invoices/{id} – Get details of an invoice (fields including attachments links).

- POST /invoices – Create an invoice record.
- Payload includes project, month, amount, counterparty info, etc.
- Only PM/Office Manager roles or above can use.
- On success, triggers the Google Sheet update and admin notification as described.
- The response returns the new invoice ID.

- PUT /invoices/{id} – Update invoice.
- Probably used to change status (but we also have a specialized method below).
- Could also allow attaching a Drive link if needed.

- PUT /invoices/{id}/status – Set status (e.g., Mark as "Paid").
- Only Admin/Accountant allowed.
- This would also log the action.
- If integrated with Google Sheet, it might also flip a flag in the sheet row or add a paid timestamp.

Authentication & User API:

- POST /auth/login – for obtaining JWT.
- Payload: username, password, 2fa_code (if applicable).
- Response: JWT token and refresh token.

POST /auth/refresh – to refresh token.

- Possibly POST /auth/bot – a special endpoint the bot might use if using a bot token instead of user password.
- For instance, the Telegram bot might authenticate using a bot token and a user identifier (the mapping of Telegram ID to user is stored), and if valid, returns a JWT for that user with possibly restricted scope.

GET /users/me – returns basic profile of logged-in user and roles (so the client app can know what to show).

(User registration for clients might be outside API scope; clients likely created by admin and given credentials).

### Notification Flow via API

- Some notifications are triggered by API calls.
- For instance, when a client uses POST /requests to create a request, the backend after inserting the request will:

Send a response to the client confirming creation,

- Then internally call routines to email the assigned engineer and message the Telegram group (this happens server-side, not via an external API but by using libraries or by creating entries in Notification doctype that ERPNext processes).
- Similarly, POST /invoices triggers backend to contact Google API and to send an email/Telegram to admin.
- These flows ensure that the API consumer (like the bot or app) doesn’t have to handle notifications – it’s done automatically.

Example API Usage Scenario: An engineer in the field has the Telegram bot:

- They send /start 123 to indicate starting work on request 123.
- Bot calls PUT /requests/123/status with status In Progress.
- The backend checks engineer’s identity and that request 123 is assigned to them, then updates it.
- It responds to bot with success, and maybe triggers an internal log.
- The bot could then reply to engineer “Marked as In Progress”.

- After finishing, they send /done 123 with maybe a summary.
- Bot might call PUT /requests/123/status to Completed.
- The system sees no ServiceReport yet, so either:

- If system requires a ServiceReport first, it responds with error “Please create ServiceReport before completing.” The bot could guide engineer to provide info for report.
- Perhaps the bot then collects a summary of work and calls POST /reports (with minimal info) to create a draft report, then automatically links it and calls status update again.
- Or,

### The system might have a simpler bypass

- allow marking Completed but behind the scenes create a stub ServiceReport automatically (maybe with the summary as description).
- The spec doesn’t explicitly say this, but something to consider to not block field ops.
- However, likely they want that separate step done by PM or office.

- In any case, after ServiceReport is eventually submitted, Admin/PM use UI or bot to /close 123 which calls PUT /requests/123/status to Closed.

### Security Guards

- Every endpoint verifies the token.
- Additionally, function-level checks ensure:

- The user’s role is allowed for that action (e.g., if a token is a Client role and tries to call /requests/123/status to mark Completed, the code will reject since clients shouldn’t do that).

### The user has access to the specific resource

- e.g., user from Customer A attempting to GET a request for Customer B gets 403.

### Rate limiting

- The API might throttle certain endpoints.
- For example, prevent brute forcing login (limit attempts by IP or user).
- Also, perhaps limit how frequently a client can call /new_request to avoid spam.

### API Implementation Note

- Since ERPNext has its own REST API, the custom backend might in many cases act as a proxy: when a request comes in, it could use Frappe’s Python API or REST to perform CRUD on the DocTypes.
- For performance and to allow additional logic, they likely use direct database access via Frappe ORM inside the same environment or via RPC.
- The custom FastAPI service might be running within the bench (as a separate service with access to frappe modules) or connect via Frappe’s REST.
- The chosen approach might be to use Frappe’s Python library (e.g., frappe.get_doc etc.) inside API route handlers to create/read docs, then commit or handle transactions as needed.
- This way all ERPNext business rules (like hooks and validations) apply automatically.
- Alternatively, they could use Frappe’s GraphQL or direct HTTP API, but having an integrated backend with direct DB access is more efficient and flexible.

### In conclusion, the API design prioritizes security and reflects the needs of external integrations

- bots for quick updates and client portal for request submission and status tracking.
- By using REST principles and JWT auth, it remains technology-agnostic so any future mobile app or integration (for instance, integrating with an IoT monitoring system that automatically creates a ServiceRequest if a sensor triggers an alert) can use these endpoints to interface with the ERP system.
