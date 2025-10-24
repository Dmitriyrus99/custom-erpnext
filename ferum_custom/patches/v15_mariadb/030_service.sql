ALTER TABLE `tabService Request`
  ADD COLUMN IF NOT EXISTS `company` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `project` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `request_type` VARCHAR(32),
  ADD COLUMN IF NOT EXISTS `status` VARCHAR(32) DEFAULT 'Open',
  ADD COLUMN IF NOT EXISTS `creation_time` DATETIME,
  ADD COLUMN IF NOT EXISTS `resolution_time` DATETIME,
  ADD COLUMN IF NOT EXISTS `assigned_engineer` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `description` TEXT;

ALTER TABLE `tabService Request`
  ADD CONSTRAINT `service_request_resolution_chk`
    CHECK (`resolution_time` IS NULL OR `creation_time` <= `resolution_time`);

ALTER TABLE `tabService Report`
  ADD COLUMN IF NOT EXISTS `company` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `service_request` VARCHAR(140),
  ADD COLUMN IF NOT EXISTS `report_date` DATE,
  ADD COLUMN IF NOT EXISTS `work_description` TEXT,
  ADD COLUMN IF NOT EXISTS `author` VARCHAR(140);
