-- Create indexes after backfill (idempotent)
CREATE UNIQUE INDEX IF NOT EXISTS `ux_invoice_company_year_no`
  ON `tabInvoice`(`company`, `invoice_year`, `invoice_no`);

CREATE INDEX IF NOT EXISTS `idx_invoice_company_date`
  ON `tabInvoice`(`company`, `invoice_date`);
