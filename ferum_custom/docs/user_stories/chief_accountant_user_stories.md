# Chief Accountant User Stories:

- 5.
- Story: Running Monthly Payroll – As the Chief Accountant, I want to calculate and disburse monthly salaries through the system, so that payroll is accurate and documented.

### Details

- It’s month-end.
- The accountant gathers attendance info, enters it into PayrollEntryCustom.

Acceptance Criteria:

- The accountant navigates to the Payroll module and creates a new Payroll Entry for say "August 2025".
- They either enter gross salary and advance for each employee manually or import from a CSV.

When they save, the system auto-calculates net pay for each employee (Gross minus Advance).

If any advance exceeds gross, the system throws a validation error or warning.

- The accountant can generate a summary report (maybe a print format or just via the UI) listing each employee and net pay.

- After verification, the accountant marks the payroll as "Completed" or "Posted".
- This could trigger a few things: lock further edits, maybe output a bank transfer file or at least allow printing pay slips for employees.

The system logs that payroll was processed by user X.

### An optional integration

- if they had employees in ERPNext, pay slips could be created for each (but not explicitly required in story).

- Accountant can confirm that totals match what will be paid from bank, and any tax computations are available for reporting.

Only accountant (and maybe admin) can see and edit this payroll; project managers or others cannot access salary info.

- 6.
- Story: Tax Report Preparation – As the Chief Accountant, I want to retrieve needed data for tax and financial reporting, so that I can prepare statutory reports (VAT, profit tax, etc.).

### Details

- Quarterly, the accountant needs figures: total revenue, total expense (subcontractor payments), payroll expenses, etc.
- Some of these can be gotten from the system.

Acceptance Criteria:

- The accountant can run an "Invoice Summary" report filtered by quarter or month that sums client invoice amounts and subcontractor invoice amounts.

They can run a "Payroll summary" for the quarter that gives total wages paid.

### For VAT

- if the company charges VAT on client invoices (maybe they do), the invoice records have VAT flag or amount.
- The accountant can filter "VAT applicable invoices" and sum their amounts to compute output VAT, and similarly see any VAT on subcontractor bills for input VAT.

They can run a "Payroll summary" for the quarter that gives total wages paid.

### For VAT

- if the company charges VAT on client invoices (maybe they do), the invoice records have VAT flag or amount.
- The accountant can filter "VAT applicable invoices" and sum their amounts to compute output VAT, and similarly see any VAT on subcontractor bills for input VAT.

The accountant exports these data (maybe via CSV export from the list view or a custom report).

All required data for government forms is obtainable: e.g., total pay to contractors (to report if needed), etc.

- If something is not directly a report, the accountant can at least easily copy or export the necessary fields from the system to plug into official accounting software.

These operations are read-only and do not compromise security (only accountant/admin can do these).
