-- PHASE 1 — Multi-Company Isolation
-- Adds company column (text) where missing, DEFERRABLE FKs to Company(name), and uniqueness helpers.
-- Idempotent and safe on reruns.
BEGIN;

-- Add company column to core business tables (safe if table missing)
DO $$
DECLARE
  tbl text;
  sql text;
  rel regclass;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'tabContract', 'tabProject', 'tabInvoice', 'tabPayment', 'tabService Request', 'tabService Report'
  ] LOOP
    EXECUTE format('SELECT to_regclass(%L)', 'public.'||tbl) INTO rel;
    IF rel IS NOT NULL THEN
      -- add company column (text) if missing
      IF NOT EXISTS (
        SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'company' AND NOT attisdropped
      ) THEN
        EXECUTE format('ALTER TABLE %I ADD COLUMN IF NOT EXISTS company text', tbl);
      END IF;
    END IF;
  END LOOP;
END$$;

-- Add DEFERRABLE FK (company -> tabCompany.name)
DO $$
DECLARE
  tbl text;
  rel regclass;
  conname text;
BEGIN
  FOREACH tbl IN ARRAY ARRAY[
    'tabContract', 'tabProject', 'tabInvoice', 'tabPayment', 'tabService Request', 'tabService Report'
  ] LOOP
    EXECUTE format('SELECT to_regclass(%L)', 'public.'||tbl) INTO rel;
    IF rel IS NOT NULL THEN
      -- only if company column exists
      IF EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'company' AND NOT attisdropped) THEN
        conname := replace(tbl, ' ', '_')||'_company_fk';
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = conname) THEN
          EXECUTE format(
            'ALTER TABLE %I ADD CONSTRAINT %I FOREIGN KEY (company) REFERENCES tabCompany(name) DEFERRABLE INITIALLY DEFERRED',
            tbl, conname
          );
        END IF;
      END IF;
    END IF;
  END LOOP;
END$$;

-- Uniqueness with company context (examples)
-- Contract: (company, lower(trim(contract_no)))
DO $$
DECLARE rel regclass; BEGIN
  SELECT to_regclass('public.tabContract') INTO rel;
  IF rel IS NOT NULL AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'company') AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'contract_no') THEN
    -- Use a stable name to avoid duplicates
    IF NOT EXISTS (
      SELECT 1 FROM pg_indexes WHERE indexname = 'ux_contract_company_no'
    ) THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_contract_company_no ON tabContract (company, LOWER(TRIM(contract_no)))';
    END IF;
  END IF;
END$$;

-- Invoice: (company, invoice_year, invoice_no) — only if columns exist
DO $$
DECLARE rel regclass; BEGIN
  SELECT to_regclass('public.tabInvoice') INTO rel;
  IF rel IS NOT NULL AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'company') AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'invoice_year') AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'invoice_no') THEN
    IF NOT EXISTS (
      SELECT 1 FROM pg_indexes WHERE indexname = 'ux_invoice_company_year_no'
    ) THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_invoice_company_year_no ON tabInvoice (company, invoice_year, invoice_no)';
    END IF;
  END IF;
END$$;

COMMIT;
