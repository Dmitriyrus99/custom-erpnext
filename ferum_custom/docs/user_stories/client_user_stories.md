# Client (Customer) User Stories:

- 17.
- Story: Submitting a Service Request via Portal/Bot – As a Client, I want to create a service request quickly through an online portal or chat, so that I can report issues without calling or emailing.

### Details

- The client notices a problem at their site.
- They decide to use the system to report it.

Acceptance Criteria (Portal scenario):

- The client logs into the Client Portal with their email and password (which were provided on onboarding).
- They see a simple interface with their company name and a list of their service projects or previous requests.

- They click "New Service Request".
- The form asks for a subject and description.
- It may allow picking the site (ServiceObject) if multiple; if they have one site, it's pre-selected.

They fill "Sprinkler system leaking in lobby, needs urgent check."

They mark priority as High (if provided) or just note "urgent" in text.

- They submit.
- The system shows a confirmation "Request #80 created.
- Our team will respond shortly."

On the backend, a new ServiceRequest is created under their customer with them as the requester.

The relevant PM/Office Manager gets notified that the client created this.

### The client can then track status by logging in later

- they see Request #80 status "Open" initially, then maybe "In Progress" after someone picks it up, etc.
- The portal page updates status field or shows timeline ("Assigned to Engineer John at 3pm").

If the client uses the Telegram bot scenario:

They open the bot chat (which they had set up earlier by verifying their account).

They send "/new_request Sprinkler leak in lobby, urgent."

The bot replies asking "Which site or project?" If multiple, the client picks from options (the bot lists their sites).

- Once provided, the bot confirms "Created Request #80 for Sprinkler leak in lobby.
- We will address it ASAP."

The rest flows similarly in backend.

### Acceptance

- The client did not have to call or email; the system captured the request directly.
- The client can refresh the portal later and see the progress without chasing via phone.

- Additionally, the client cannot see any internal fields like which engineer or cost, just the basic status updates (maybe they see comments if PM leaves any).

- 18.
- Story: Checking Project Documents – As a Client, I want to download the completed work report and invoice for a finished job via the portal, so that I have all necessary documentation for my records.

Details: After a service call is done, the client wants copies of the paperwork.

Acceptance Criteria:

The client logs in and navigates to their project "Annual Maintenance Contract 2025".

- They see a section "Service Reports" or maybe the specific request which is closed.
- They click it and see details including a link to "Service Report PDF" (perhaps the file name or a button "Download Report").

- They click and it downloads the signed work report (which was uploaded by PM).
- Or it could open in browser.

- They also see an "Invoice #INV-1001" listed under invoices for that project (if they allow clients to see their invoices).
- They click that and get the PDF invoice.

If the portal isn't showing invoice, at least they got it via email; but ideally, portal shows any client-facing docs.

- The client verifies the work report is signed by their representative (scanned copy) and the invoice amount matches their records.
- All good.

If anything was missing, the client would contact the PM, but in system everything is accessible.

### Acceptance

- A test client can successfully retrieve attachments for a closed request (the system ensures client permission on those attachments is allowed since it's tied to their customer and the security model permits it).

They cannot see any internal docs not meant for them (like subcontractor invoices or internal notes).

The client feels more self-sufficient and trusts the online portal for transparency.
