ALTER TABLE `tabContract`
  ADD COLUMN IF NOT EXISTS `company` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `customer` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `project` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `contract_no` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `contract_no_normalized` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `date_start` DATE,
  ADD COLUMN IF NOT EXISTS `date_end` DATE,
  ADD COLUMN IF NOT EXISTS `amount_max` DECIMAL(18,2),
  ADD COLUMN IF NOT EXISTS `status` VARCHAR(20) DEFAULT 'active',
  ADD UNIQUE KEY IF NOT EXISTS `ux_contract_company_no`(`company`, `contract_no_normalized`);

ALTER TABLE `tabContract`
  ADD CONSTRAINT `contract_date_range_chk`
    CHECK (`date_start` IS NULL OR `date_end` IS NULL OR `date_start` <= `date_end`);

ALTER TABLE `tabContract Stage`
  ADD COLUMN IF NOT EXISTS `contract` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `stage_no` INT,
  ADD COLUMN IF NOT EXISTS `name_stage` VARCHAR(255),
  ADD COLUMN IF NOT EXISTS `period_from` DATE,
  ADD COLUMN IF NOT EXISTS `period_to` DATE,
  ADD COLUMN IF NOT EXISTS `amount_plan` DECIMAL(18,2),
  ADD UNIQUE KEY IF NOT EXISTS `ux_contract_stage_no`(`contract`, `stage_no`);
