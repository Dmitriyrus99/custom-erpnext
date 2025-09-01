# Module Breakdown

- This section provides an overview of the custom modules that extend ERPNext for Ferum's operations.
- Each file below documents a specific module and its responsibilities.

## Modules

- [Project & Contract Management](project_contract_management_module.md)
- [Service Request Management](service_request_management_module.md)
- [Work Report & Completion](work_report_completion_module.md)
- [Document Management](document_management_module.md)
- [Invoicing](invoicing_module.md)
- [HR & Payroll](hr_payroll_module.md)
- [Notifications & Communications](notifications_communications_module.md)
- [Analytics & Reporting](analytics_reporting_module.md)

## Module Interactions

- Projects create the framework for service work, linking service objects and establishing contract details.
- Service requests tie into projects and objects, capturing issues reported by clients.
- Work reports close requests and feed financial data into the invoicing module and labor metrics into HR & Payroll.
- The document management module stores attachments shared across these workflows, while the notifications module broadcasts key events to users.
- Analytics aggregates data from all modules to provide operational insights.
- All modules leverage ERPNext DocTypes, permissions and APIs to maintain consistency and integrate with the broader ERP system.
