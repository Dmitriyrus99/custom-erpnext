-- Optional uniqueness for (company, invoice_year, invoice_no)
DO $$
DECLARE rel regclass; BEGIN
  SELECT to_regclass('public.tabInvoice') INTO rel;
  IF rel IS NOT NULL AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'company') AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'invoice_year') AND
     EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'invoice_no') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_invoice_company_year_no') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_invoice_company_year_no ON tabInvoice (company, invoice_year, invoice_no)';
    END IF;
  END IF;
END$$;
