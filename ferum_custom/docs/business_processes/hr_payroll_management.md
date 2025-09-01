# HR & Payroll Management (Employee Time and Payroll Accounting)

### Figure 5: HR & Payroll BPMN

![HR & Payroll BPMN](../images/hr_payroll_management_process.svg)

This process deals with tracking employee work and calculating salaries, handled largely within the ERPNext HR module but with customizations for the company’s needs.
- The company has a relatively small staff (under 20 employees), so simplicity and accuracy are key.

### Time & Attendance Tracking

- The HR department (Administrative office) maintains records of each employee’s work schedule, absences, and overtime.
- This may involve keeping a roster or using ERPNext’s built-in Attendance and Leave Application doctypes.
- By the  end of each pay period (monthly or quarterly), they should have data on each employee’s working days, leave days, sick leave, etc..
- In our system, some of this data might be entered directly (e.g., Office Manager enters sick leaves into the system, or employees apply for leave via the portal).

### Payroll Entry Preparation

- When it’s time to run payroll, the Chief Accountant uses the custom PayrollEntryCustom DocType to compile salary calculations.
- This custom doctype is an extension of ERPNext’s Payroll Entry, adapted for the company’s specific payroll rules (for instance, handling advances to subcontractors or unique payment structures).
- The PayrollEntryCustom likely includes fields for each employee’s gross pay, any advance paid earlier in the month, deductions, and the resulting net pay (total payable).
- The accountant creates a Payroll Entry for the period (say “July 2025 Payroll”) and enters or imports each employee’s data (if not automatically fetched from Salary Structures).

### Automation

- A server-side script on PayrollEntryCustom automates calculation of the net salary for each employee by subtracting any advance payments from the gross amount.
- This logic ensures that the final payable amount is accurate (salary minus advance or other deductions).
- It might also aggregate totals for the whole payroll run.
- If any required info is missing (like an employee’s hours or rate), validation will prompt the user to fill it.

- Once verified, the payroll entry can be submitted, and the system might generate pay slips for each employee (if following ERPNext’s standard approach, though with a small team, the accountant might simply use the payroll entry as the record and not individual payslips).

### Payment Execution

- After calculating payroll, the accountant proceeds to execute payments – typically outside the system via bank transfers.
- However, Ferum Customizations can assist by producing a summary of who gets paid what.
- For instance, an export of the payroll entry can be used to upload a payment batch to the bank.
- The accountant then marks the PayrollEntryCustom or related records as paid (or simply considers the submission as final).

### Reporting

- The system helps generate needed financial and tax reports.
- For example, it can track total payroll cost for the month, taxes withheld, etc.
- The Chief Accountant can use these figures for statutory reports: VAT returns (if applicable on certain expenses), income tax and social contributions (payroll tax reports like 6-НДФЛ in Russia).
- These reports might not be fully automated in ERPNext (depending on localization), but the data is available to be extracted.
- For instance, the accountant can run a report on PayrollEntryCustom to get total wages and then manually prepare tax forms.

### User Roles & Permissions

- Only HR/Accounting roles can access payroll data.
- The system ensures that payroll records (salaries) are confidential – e.g., only the Chief Accountant and maybe the Administrator have access to PayrollEntryCustom documents.
- This is enforced by role permission settings in ERPNext.
- Regular project managers or engineers have no access to HR data.

- In summary, the HR/Payroll process in Ferum Customizations automates the salary calculation step (reducing manual errors in computing net pay) and ensures records of payroll are kept in the system for future reference (useful for audits or financial analysis).
- While payouts themselves and advanced HR features (like attendance tracking automation) might be handled partially outside or manually, the system provides a central place for payroll accounting that ties into projects (for example, labor costs could be allocated to an internal project “Office Payroll” for budgeting purposes).
- This integration means management can consider labor costs when analyzing project profitability, if desired.
