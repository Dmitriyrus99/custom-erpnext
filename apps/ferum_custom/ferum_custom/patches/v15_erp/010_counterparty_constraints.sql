BEGIN;
-- Counterparty uniqueness (per company) guards
DO $$
DECLARE rel regclass; BEGIN
  SELECT to_regclass('public.tabCounterparty') INTO rel;
  IF rel IS NOT NULL THEN
    -- Partial unique by (company, inn) when inn is not null
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_counterparty_company_inn') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_counterparty_company_inn ON tabCounterparty (company, inn) WHERE inn IS NOT NULL';
    END IF;
    -- Case-insensitive short-name uniqueness per company
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_counterparty_company_name_short') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_counterparty_company_name_short ON tabCounterparty (company, lower(name_short))';
    END IF;
  END IF;
END$$;
COMMIT;
