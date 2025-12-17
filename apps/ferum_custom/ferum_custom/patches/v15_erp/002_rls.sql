-- PHASE 1 (cont.) — RLS example for company isolation
-- Uses current_setting('erp.company_id') to scope visibility per connection.
-- Extend similarly to other tables as needed.
DO $$
BEGIN
  -- Enable RLS only if table exists
  IF to_regclass('public.tabInvoice') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE tabInvoice ENABLE ROW LEVEL SECURITY';
    -- Policy name is stable and replaced idempotently
    IF EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public' AND tablename = 'tabInvoice' AND policyname = 'company_isolation_invoice') THEN
      EXECUTE 'DROP POLICY company_isolation_invoice ON tabInvoice';
    END IF;
    EXECUTE $$CREATE POLICY company_isolation_invoice
              ON tabInvoice
              USING (company = current_setting('erp.company_id'))$$;
  END IF;
END$$;

-- Repeat for other tables (Contract, Project, Payment, "Service Request", "Service Report", etc.) as required.
