-- Idempotent migration for Ferum Customizations (MariaDB)
-- Adds invoice numbering fields and supporting indexes where missing.

ALTER TABLE `tabInvoice`
  ADD COLUMN IF NOT EXISTS `invoice_no` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `invoice_year` INT,
  ADD COLUMN IF NOT EXISTS `contract` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `customer` VARCHAR(140);

-- Uniqueness per (company, year, number)
CREATE UNIQUE INDEX IF NOT EXISTS `ux_invoice_company_year_no`
  ON `tabInvoice`(`company`, `invoice_year`, `invoice_no`);

-- Helpful filters
CREATE INDEX IF NOT EXISTS `idx_invoice_company_date`
  ON `tabInvoice`(`company`, `invoice_date`);

-- Payment integrity
ALTER TABLE `tabPayment`
  ADD CONSTRAINT `payment_amount_positive_chk` CHECK (`amount` > 0);

-- Allocation integrity
ALTER TABLE `tabPayment Allocation`
  ADD CONSTRAINT `payment_allocation_positive_chk` CHECK (`amount` > 0);
