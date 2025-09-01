# HR & Payroll Module

### Responsibilities

- Extend ERPNext’s HR for the company’s simple payroll process.
- Keep track of employees, their working hours (manually), and compute salaries with any deductions (advances) through a custom payroll entry.

### DocTypes

- PayrollEntryCustom, and uses standard Employee, Attendance, Leave possibly.
- If ERPNext’s built-in Payroll Entry could be extended via custom fields and scripts, they might have done that instead of a new doctype.
- But the spec suggests a custom one, perhaps to avoid altering core doctype.

Key Fields:

### PayrollEntryCustom

- period_start, period_end (or month), posting_date, a child table of PayrollEntryItem (could contain employee, gross_pay, advance, net_pay), total_payroll_amount, status (Draft, Completed).

PayrollEntryItem (if exists as child): employee, gross, advance, net (the script would fill net = gross - advance).

- Alternatively, they might not use a child table but rather rely on adding advance fields to ERPNext Salary Slip or something.
- But simpler is a child table for summary since only ~20 employees.

Automation & Hooks:

### On PayrollEntryCustom validate

- loop through each entry (or each linked employee) and calculate net = gross - advance.
- Ensure net is not negative (maybe adjust if advance > gross, or flag it).

- Possibly integrate with ERPNext’s Loan or Advance doctype if they record advances separately, but given small scale, they may just input advance amounts manually for each pay period.

### On PayrollEntryCustom submit

- not much, maybe mark related Salary Slip docs if they used that, or just mark status Completed.

- If any payslips are generated, then ERPNext’s payroll processor might be used.
- But since they explicitly mention a custom doctype, likely they are doing it in a simpler aggregated way.

- The system might produce a summary report of payroll which could be exported to an accounting system (like for bank transfer or for posting into accounting).

Integrations:

### Google Sheets

- They might maintain an internal Google Sheet for HR as well, but nothing indicated.
- Probably not necessary.

Prometheus monitoring: one could track number of employees or total payroll cost as a metric, but that’s minor.

- Possibly integration with Telegram bot for notifications if desired (like notifying an employee of their salary credited, but that’s beyond scope).

Email: Not likely needed, but maybe notify the Director that payroll of X amount was executed this month, etc.

### External Accounting

- similar to invoices, maybe after computing payroll, the totals are entered into 1C or another system for actual disbursement and accounting records (since ERPNext might not be primary accounting system here, given local requirements).

UI Components:

- ERPNext Form for PayrollEntryCustom – perhaps resembling the standard Payroll Entry but simpler.
- Might allow selecting a Period and auto-filling employees, though likely they just manually add entries because of small staff.

- Possibly they just use ERPNext’s Salary Structure and Salary Slip but customizing one calculation.
- The spec though specifically calls out a custom doc, implying they didn’t want to engage full payroll module.

Reports: a payroll report for the period to review before finalizing.

- This module is relatively self-contained and primarily for the accountant’s use, ensuring one central place for salary calculations and records which can be audited and referenced (especially for seeing labor costs).
