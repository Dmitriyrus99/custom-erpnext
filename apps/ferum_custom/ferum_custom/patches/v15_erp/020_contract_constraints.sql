BEGIN;
-- Contract invariants and uniqueness
DO $$
DECLARE rel regclass; conname text; BEGIN
  SELECT to_regclass('public.tabContract') INTO rel;
  IF rel IS NOT NULL THEN
    conname := 'chk_contract_dates';
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = conname) THEN
      EXECUTE 'ALTER TABLE tabContract ADD CONSTRAINT chk_contract_dates CHECK (date_start IS NULL OR date_end IS NULL OR date_start <= date_end) NOT VALID';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_contract_company_no') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_contract_company_no ON tabContract (company, lower(trim(contract_no)))';
    END IF;
  END IF;
END$$;
COMMIT;
