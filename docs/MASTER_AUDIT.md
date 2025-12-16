# Ferum Customizations - Master Audit Notes

This document consolidates key architectural decisions, findings, and critical notes for the Ferum Customizations project.

## Stage 1 & 2 Summary

- **Stage 1: Financial & Currency Stabilization**
  - Successfully applied patch `fix_currency_and_pricelist`.
  - Verified absence of critical errors in logs related to currency exchange rate lookups.

- **Stage 2: Payment & Procurement Minimal Viability**
  - Default bank and cash accounts successfully assigned to companies 'Ferum Co' and 'Ferum Demo' via SQL.
  - Supplier records ('Supplier-FC', 'Supplier-FD') created successfully, noting that `tabSupplier` does not have a `company` field.

## Architectural Notes:

**Supplier DocType Behavior:**
Supplier в ERPNext не имеет поля company.
Supplier является глобальной сущностью, а company-scope обеспечивается через:

- Purchase Invoice
- Accounts
- Permissions

Это избавит от будущих ложных «багов».
