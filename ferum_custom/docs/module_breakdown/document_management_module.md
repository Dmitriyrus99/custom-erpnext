# Document Management Module (File Handling)

### Responsibilities

- Provide unified handling of file attachments across the system and integrate with Google Drive for storage.

### DocTypes

- CustomAttachment (and potentially File if using ERPNext’s built-in, but likely not needed since CustomAttachment can reference the ERPNext File or external link).
- Also child tables like RequestPhotoAttachmentItem and ServiceReportDocumentItem which act as linking tables.

Key Fields:

### CustomAttachment

- file_name, file_url or file_id (if storing the Drive file ID), file_type (image, pdf, etc.), attached_to_doctype, attached_to_name (or it might not need if using separate link tables), uploaded_by, uploaded_on.

- If using ERPNext’s File doctype behind the scenes, CustomAttachment could even just be a proxy reference to it.
- But since they plan direct Drive storage, they might bypass ERPNext File.

- Child link tables have minimal fields (they rely on the parent doc for context and on CustomAttachment for file details).

Automation & Hooks:

- On any doctype that uses attachments, they might override the default attach mechanism.
- Possibly they have a custom form UI (like a section with a table to add attachments, which creates RequestPhotoAttachmentItem linking to an existing CustomAttachment or uploading a new one).

### File Upload Process

- Likely implemented in the custom backend or a frappe endpoint: when a file is uploaded via form or bot, the system:

Saves the file temporarily in ERPNext’s private or public files (if using Frappe file upload).

Creates a CustomAttachment record with metadata.

- If upload is via the backend (like through the bot), the file might be directly streamed to Drive and not even stored on ERPNext server to save space.
- In that case, a CustomAttachment is created with file_id or Drive link.

Adds a child table entry linking CustomAttachment to the parent doc.

### On CustomAttachment on_trash

- as described, delete file from Drive if it exists.
- This function would use the Google Drive API with the file ID stored.

### On CustomAttachment validate

- possibly ensure file has a reference or content.
- Might also enforce a file size limit or type whitelist.

### Synchronization job

- It’s possible they have a scheduled job that goes through new attachments and ensures they are on Drive, in case some were uploaded when offline, etc.
- But if implemented in real-time on upload, maybe not needed.

Also, if using any local storage fallback, they might schedule cleanup of local files after upload to Drive.

Integrations:

### Google Drive

- central to this module.
- They would have a Google API setup with credentials (service account or OAuth token).
- The integration might define a base folder (like a Drive folder ID under which all files go).
- If not separating by project, maybe a naming scheme e.g., Project123-ServiceRequest456-BeforePhoto1.jpg as the file name.
- If separating, then folder per project or per doc type.

- They might implement the Drive integration in the custom backend (with a Python Google client) or use a Google Drive Frappe integration if one exists.

- Potential integration with DocuSign or E-sign for the future if needed (not in current scope, but sometimes for signed acts).

UI Components:

- In ERPNext forms, instead of the standard attachment sidebar, they might have custom sections for attachments.
- For example, ServiceRequest form could have a table “Photos” which lists attachments, and a button “Attach Photo” that opens file dialog.

They likely disabled or bypassed the default attachment sidebar to streamline things.

- For large files (photos), maybe they only store a thumbnail or link in ERPNext and the actual file is only in Drive to save database space.

- Users will mostly interact with attachments as part of the relevant form (Project, Request, Report).
- Admins could have an Attachment List (all CustomAttachment entries) for housekeeping.

- This module ensures files are not siloed on one user’s computer or lost in emails – they’re systematically stored and linked to context.
- Also, by using Drive, it solves storage scaling and backup automatically (Drive itself is robust).
