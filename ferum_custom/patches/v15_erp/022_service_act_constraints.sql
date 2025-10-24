DO $$
BEGIN
  IF to_regclass('public."tabService Act"') IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_service_act_unique') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_service_act_unique ON "tabService Act"(contract, act_no)';
    END IF;
  END IF;
END$$;

