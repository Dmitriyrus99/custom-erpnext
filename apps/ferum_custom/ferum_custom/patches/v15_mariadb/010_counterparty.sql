ALTER TABLE `tabCounterparty`
  ADD COLUMN IF NOT EXISTS `company` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `name_full` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `name_short` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `inn` VARCHAR(20),
  ADD COLUMN IF NOT EXISTS `kpp` VARCHAR(20),
  ADD COLUMN IF NOT EXISTS `address` TEXT,
  ADD COLUMN IF NOT EXISTS `contacts` TEXT,
  ADD UNIQUE KEY IF NOT EXISTS `ux_company_inn`(`company`, `inn`),
  ADD UNIQUE KEY IF NOT EXISTS `ux_company_name_short`(`company`, `name_short`);

ALTER TABLE `tabProject`
  ADD COLUMN IF NOT EXISTS `company` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `code` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `name_project` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `address` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `customer` VARCHAR(140),
  ADD UNIQUE KEY IF NOT EXISTS `ux_project_company_code`(`company`, `code`);
