# Project & Contract Management Module

### Responsibilities

- Manage service contracts (projects) and the inventory of service objects under those contracts.
- This module ensures that new projects are properly configured and that service objects are tracked against their contracts without conflicts.

### DocTypes

- ServiceProject, ServiceObject, ProjectObjectItem.
- The ServiceProject DocType holds project details (name, client, start/end dates, contract amount, status, etc.).
- ServiceObject holds info on each maintenance object (name, location, customer, etc.).
- ProjectObjectItem is a child table on ServiceProject listing linked ServiceObjects.

### Data Relationships

- ServiceProject has a child table objects (ProjectObjectItem) linking to ServiceObject.
- Also, ServiceObject may have a direct link to its current project (the field project), allowing quick lookup of which project an object is under.

Key Fields:

### ServiceProject

- customer (Link to Customer), project_name, start_date, end_date, status (Select: e.g.
- Planned, Active, Completed), total_amount (contract value), project_manager (Link to User/Employee).

### ServiceObject

- object_name, address/location, customer, type (e.g.
- fire alarm panel, sprinkler, etc.), project (Link to ServiceProject, optional).

ProjectObjectItem: service_object (Link to ServiceObject) + maybe remarks or included scope.

Automation & Hooks:

### On ServiceProject validate

- ensure date consistency and unique objects.
- A method check_dates_and_amount validates dates and that total_amount is not negative.
- _validate_unique_objects checks the objects table: no duplicate entries and that none of those objects are already linked to another project.
- If a duplicate or conflict is found, it throws a clear error (e.g., “Service Object X is already linked to project Y”).

### On ServiceObject validate

- ensure uniqueness of object name within a project.
- The code _ensure_unique_per_project queries if another ServiceObject with the same name exists for the same project.
- This prevents creating two ServiceObject records that refer to essentially the same asset under one project.

### On ServiceObject on_trash

- prevent deletion if any active ServiceRequest references this object.
- It checks for Service Request where status is not Closed for this object; if found, deletion is blocked with an error “Cannot delete object linked to active service requests.”.

### Possibly on ServiceProject on_update

- could trigger notifications (e.g., when status changes to Active, send welcome email as described earlier).
- This might be done via an ERPNext Notification rule rather than code.

Integrations: When a new project is created or a project’s key fields change, the module can integrate with:

Email: Auto-send a templated email to the client on project kickoff.

Drive: Optionally, create a folder in Google Drive for the project (if the design chooses per-project folders).

### External Systems

- Export project/customer info for accounting systems if needed (could be manual export or future integration).

Bot Notification: Inform relevant team chats about new project (enhancement).

UI Components:

- ERPNext Form for ServiceProject (with a section for contract info and a child table for objects).
- A custom script on this form might filter the ServiceObject list to only those belonging to the same customer to avoid mix-ups.

ERPNext List/Report: a list of projects with color indicators (e.g., Active vs Completed).

### React Frontend

- a project list view and detail page showing all related info (requests, invoices, etc.) for that project.

### Dashboard

- possibly a custom Project Dashboard showing metrics like “# of open requests” or total billed amount, using ERPNext’s dashboard framework.

- By enforcing consistent project setup and linking all downstream data (requests, reports, invoices) to the project, this module provides the foundation for contract-based tracking of work and finances.
