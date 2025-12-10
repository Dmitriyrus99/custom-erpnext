# Project & Contract Management Module

### Responsibilities

- Manage contracts (projects) and the inventory of assets under those contracts.
- This module ensures that new projects are properly configured and that assets are tracked against their contracts without conflicts.

### DocTypes

- Project, Asset.
- The Project DocType holds project details (name, client, start/end dates, contract amount, status, etc.).
- Asset holds info on each maintenance asset (name, location, customer, etc.).

### Data Relationships

- Project is linked to Asset directly or via a linking mechanism.
- Also, Asset may have a direct link to its current project (the field project), allowing quick lookup of which project an asset is under.

Key Fields:

### Project

- customer (Link to Customer), project_name, start_date, end_date, status (Select: e.g.
- Planned, Active, Completed), total_amount (contract value), project_manager (Link to User/Employee).

### Asset

- object_name, address/location, customer, type (e.g.
- fire alarm panel, sprinkler, etc.), project (Link to Project, optional).
Automation & Hooks:

### On Project validate

- ensure date consistency and unique assets.
- A method check_dates_and_amount validates dates and that total_amount is not negative.
- \_validate_unique_assets checks for unique assets and that none are already linked to another active project.
- If a duplicate or conflict is found, it throws a clear error (e.g., “Asset X is already linked to project Y”).

### On Asset validate

- ensure uniqueness of asset name within a project.
- The code \_ensure_unique_per_project queries if another Asset with the same name exists for the same project.
- This prevents creating two Asset records that refer to essentially the same asset under one project.

### On Asset on_trash

- prevent deletion of any active Issue references this asset.
- It checks for Issue where status is not Closed for this asset; if found, deletion is blocked with an error “Cannot delete asset linked to active issues.”.

### Possibly on Project on_update

- could trigger notifications (e.g., when status changes to Active, send welcome email as described earlier).
- This might be done via an ERPNext Notification rule rather than code.

Integrations: When a new project is created or a project’s key fields change, the module can integrate with:

Email: Auto-send a templated email to the client on project kickoff.

Drive: Optionally, create a folder in Google Drive for the project (if the design chooses per-project folders).

### External Systems

- Export project/customer info for accounting systems if needed (could be manual export or future integration).

Bot Notification: Inform relevant team chats about new project (enhancement).

### UI Components

- ERPNext Form for Project (with a section for contract info and a table for assets).
- A custom script on this form might filter the Asset list to only those belonging to the same customer to avoid mix-ups.

ERPNext List/Report: a list of projects with color indicators (e.g., Active vs Completed).

### React Frontend

- a project list view and detail page showing all related info (issues, invoices, etc.) for that project.

### Dashboard

- possibly a custom Project Dashboard showing metrics like “# of open issues” or total billed amount, using ERPNext’s dashboard framework.

- By enforcing consistent project setup and linking all downstream data (issues, timesheets, invoices) to the project, this module provides the foundation for contract-based tracking of work and finances.
