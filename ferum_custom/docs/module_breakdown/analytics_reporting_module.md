# Analytics & Reporting Module

Responsibilities: Generate analytics dashboards and custom reports for management, beyond the standard ERPNext reports.

### Components

- Could be partly outside ERPNext (in backend code producing data for bot or external dashboard) and partly inside ERPNext (printable or on-screen reports).

Key Reports/Metrics:

### Projects

- profitability (sum of client invoices minus subcontractor invoices per project), number of open requests per project, etc.

### Requests

- average resolution time, number of requests per month, breakdown by type (routine vs emergency), engineer performance (how many each closed).

Financial: total receivables, payables, aging of invoices (how long unpaid).

### HR

- maybe staff utilization, but with 20 employees likely simple, though they might track how many requests each engineer handles (which can be an indicator of workload).

Implementation:

### Some metrics can be pre-calculated and stored (like in fields on Project

- e.g., project_cost, project_revenue updated whenever an invoice is added or changed).

Others computed on the fly via queries.

- Possibly a scheduled task that every night computes key metrics and stores in a cache table or as singletons that the bot can read.
- But given not huge data, on-demand queries are fine.

The Analytics backend may use direct SQL or frappe ORM to gather data, especially if needing to join across doctypes.

Ensuring permission: only certain roles can access analytics (Admin, Director primarily).

UI:

Telegram Bot: as described, can output KPI summaries on command.

- Grafana (if set up) or Google Data Studio, etc., could be used by connecting to the Google Sheet (for financial metrics) or directly to the database.
- Not mentioned, but an option.

### ERPNext Dashboards

- They might configure some dashboard charts on the desk homepage for Admin (like a chart of requests by month).

### Standard reports

- maybe custom Script Reports in ERPNext for things like “Open Requests by Engineer” or “Invoice Summary by Project”.

### Monitoring integration

- Overlaps with Prometheus if they track metrics like request count – but that’s more infra.
- The analytics here is more business metrics.

While not explicitly called a module in ERPNext terms, it’s an important capability allowing data-driven decisions.
