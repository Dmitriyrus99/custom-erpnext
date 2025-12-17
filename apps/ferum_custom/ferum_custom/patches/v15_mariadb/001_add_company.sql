ALTER TABLE `tabContract`      ADD COLUMN IF NOT EXISTS `company` VARCHAR(140);
ALTER TABLE `tabProject`       ADD COLUMN IF NOT EXISTS `company` VARCHAR(140);
ALTER TABLE `tabInvoice`       ADD COLUMN IF NOT EXISTS `company` VARCHAR(140);
ALTER TABLE `tabPayment`       ADD COLUMN IF NOT EXISTS `company` VARCHAR(140);
ALTER TABLE `tabService Request` ADD COLUMN IF NOT EXISTS `company` VARCHAR(140);
ALTER TABLE `tabService Report`  ADD COLUMN IF NOT EXISTS `company` VARCHAR(140);

CREATE INDEX IF NOT EXISTS `idx_contract_company` ON `tabContract`(`company`);
CREATE UNIQUE INDEX IF NOT EXISTS `ux_project_company_code`
  ON `tabProject`(`company`,`code`);
