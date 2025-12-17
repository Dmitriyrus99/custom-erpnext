DO $$
BEGIN
  IF to_regclass('public."tabContract Stage"') IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_contract_stage_unique') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_contract_stage_unique ON "tabContract Stage"(contract, stage_no)';
    END IF;
  END IF;
END$$;
