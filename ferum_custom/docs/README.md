# Ferum Customizations — MariaDB Architecture
* Multi-company isolation (User Permission)
* Normalized Contracts, Invoices, Payments
* Views for analytics (vw_invoice_balance, vw_contract_overview)
* Triggers for integrity and auto-status
* ETL scripts for data import
* Tests and documentation

---
### MariaDB Migration Notes
* All triggers moved to Python patch (`041_triggers.py`)
* SQL patches applied via `apply_schema.py`
* Conflicts with Frappe ORM avoided by converting `CREATE TABLE` → `ALTER TABLE`
* Added to `patches.txt` for automatic migration
* Verified with `bench migrate` and pytest (see repo README for latest status)

---
### MariaDB Schema Deployment (Gemini → Codex)
* YAML schema parsed and deployed as SQL + Python patches
* Triggers moved to 041_triggers.py
* Stored procedures moved to 042_procedures.py
* All SQL scripts executed through apply_schema.py
* Connected to patches.txt for automatic migrations
* Verified via bench migrate & pytest
