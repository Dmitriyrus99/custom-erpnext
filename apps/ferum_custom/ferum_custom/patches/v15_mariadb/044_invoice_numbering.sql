-- Add numbering fields for Invoice (idempotent)
ALTER TABLE `tabInvoice`
  ADD COLUMN IF NOT EXISTS `invoice_no` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `invoice_year` INT;
