BEGIN;
-- Payment invariants and helper indexes
DO $$
DECLARE rel regclass; BEGIN
  -- Positive amount check
  SELECT to_regclass('public.tabPayment') INTO rel;
  IF rel IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='chk_payment_amount') THEN
      EXECUTE 'ALTER TABLE tabPayment ADD CONSTRAINT chk_payment_amount CHECK (amount > 0) NOT VALID';
    END IF;
  END IF;

  -- Unique allocation per (payment, invoice)
  SELECT to_regclass('public."tabPayment Allocation"') INTO rel;
  IF rel IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ux_payalloc_unique') THEN
      EXECUTE 'CREATE UNIQUE INDEX ux_payalloc_unique ON "tabPayment Allocation"(payment, invoice)';
    END IF;
  END IF;

  -- Partial index for open invoices (Draft, Sent)
  SELECT to_regclass('public.tabInvoice') INTO rel;
  IF rel IS NOT NULL THEN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='idx_invoice_open') THEN
      EXECUTE $$CREATE INDEX idx_invoice_open ON tabInvoice(company, invoice_date) WHERE status IN ('Sent','Draft')$$;
    END IF;
  END IF;
END$$;
COMMIT;
