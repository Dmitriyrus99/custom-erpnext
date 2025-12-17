-- Service Request invariants adapted to existing fields
DO $$
DECLARE rel regclass; conname text; BEGIN
  SELECT to_regclass('public."tabService Request"') INTO rel;
  IF rel IS NOT NULL THEN
    conname := 'chk_sr_times';
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = conname) THEN
      EXECUTE 'ALTER TABLE "tabService Request" ADD CONSTRAINT chk_sr_times CHECK (actual_end_datetime IS NULL OR reported_datetime <= actual_end_datetime) NOT VALID';
    END IF;
  END IF;
END$$;
