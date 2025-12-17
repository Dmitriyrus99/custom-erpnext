-- BRIN and helper indexes (guarded by existence)
DO $$
DECLARE rel regclass; BEGIN
  -- BRIN on date columns (parents)
  SELECT to_regclass('public.tabInvoice') INTO rel;
  IF rel IS NOT NULL AND EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname='invoice_date') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='brin_invoice_date') THEN
      EXECUTE 'CREATE INDEX brin_invoice_date ON tabInvoice USING BRIN (invoice_date)';
    END IF;
  END IF;
  SELECT to_regclass('public.tabPayment') INTO rel;
  IF rel IS NOT NULL AND EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname='trx_date') THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='brin_payment_date') THEN
      EXECUTE 'CREATE INDEX brin_payment_date ON tabPayment USING BRIN (trx_date)';
    END IF;
  END IF;

  -- FK/search helpers
  IF to_regclass('public.tabInvoice') IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='idx_invoice_customer') THEN
      EXECUTE 'CREATE INDEX idx_invoice_customer ON tabInvoice(customer)';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='idx_invoice_contract') AND EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'public.tabInvoice'::regclass AND attname = 'contract') THEN
      EXECUTE 'CREATE INDEX idx_invoice_contract ON tabInvoice(contract)';
    END IF;
  END IF;
  IF to_regclass('public.tabPayment') IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='idx_payment_counterparty') THEN
      EXECUTE 'CREATE INDEX idx_payment_counterparty ON tabPayment(counterparty)';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='idx_payment_article') THEN
      EXECUTE 'CREATE INDEX idx_payment_article ON tabPayment(article)';
    END IF;
  END IF;
END$$;
