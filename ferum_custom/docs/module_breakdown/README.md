# Module Breakdown

- This section provides an overview of the custom modules that extend ERPNext for Ferum's operations.
- Each file below documents a specific module and its responsibilities.

## Modules

- [Project & Contract Management](project_contract_management_module.md)
- [Issue Management](issue_management_module.md)
- [Timesheet & Work Completion](timesheet_work_completion_module.md)
- [Document Management](document_management_module.md)
- [Invoicing](invoicing_module.md)
- [HR & Payroll](hr_payroll_module.md)
- [Notifications & Communications](notifications_communications_module.md)
- [Analytics & Reporting](analytics_reporting_module.md)

## Module Interactions

- Projects create the framework for service work, linking assets and establishing contract details.
- Issues tie into projects and assets, capturing issues reported by clients.
- Timesheets close issues and feed financial data into the invoicing module and labor metrics into HR & Payroll.
- The document management module stores attachments shared across these workflows, while the notifications module broadcasts key events to users.
- Analytics aggregates data from all modules to provide operational insights.
- All modules leverage ERPNext DocTypes, permissions and APIs to maintain consistency and integrate with the broader ERP system.
