DO $$
DECLARE rel regclass; BEGIN
  SELECT to_regclass('public.tabProject') INTO rel;
  IF rel IS NOT NULL AND EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname='company') AND EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname='code') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_project_company_code') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_project_company_code ON tabProject (company, code)';
    END IF;
  END IF;
END$$;
