-- Trigger functions to enforce allocation limits and auto-status on invoices

DO $$
BEGIN
  IF to_regclass('public."tabPayment Allocation"') IS NULL THEN
    RETURN; -- nothing to do if allocation table absent
  END IF;

  -- Enforce that allocations do not exceed invoice or payment totals
  CREATE OR REPLACE FUNCTION fn_check_allocation_limits() RETURNS trigger AS $$
  DECLARE
    inv_total NUMERIC;
    inv_sum   NUMERIC;
    pay_total NUMERIC;
    pay_sum   NUMERIC;
  BEGIN
    -- Load and lock invoice and payment totals
    SELECT amount INTO inv_total FROM tabInvoice WHERE name = NEW.invoice FOR UPDATE;
    SELECT amount INTO pay_total FROM tabPayment WHERE name = NEW.payment FOR UPDATE;

    IF inv_total IS NULL THEN
      RAISE EXCEPTION 'Invoice % not found', NEW.invoice;
    END IF;
    IF pay_total IS NULL THEN
      RAISE EXCEPTION 'Payment % not found', NEW.payment;
    END IF;

    -- Sum existing allocations excluding this row (for UPDATE) or all (for INSERT)
    SELECT COALESCE(SUM(amount), 0) INTO inv_sum
      FROM "tabPayment Allocation"
      WHERE invoice = NEW.invoice AND (NEW.name IS NULL OR name <> NEW.name);

    IF inv_sum + NEW.amount > inv_total THEN
      RAISE EXCEPTION 'Allocation exceeds invoice total';
    END IF;

    SELECT COALESCE(SUM(amount), 0) INTO pay_sum
      FROM "tabPayment Allocation"
      WHERE payment = NEW.payment AND (NEW.name IS NULL OR name <> NEW.name);

    IF pay_sum + NEW.amount > pay_total THEN
      RAISE EXCEPTION 'Allocation exceeds payment total';
    END IF;

    RETURN NEW;
  END$$ LANGUAGE plpgsql;

  DROP TRIGGER IF EXISTS trg_check_alloc ON "tabPayment Allocation";
  CREATE TRIGGER trg_check_alloc
    BEFORE INSERT OR UPDATE ON "tabPayment Allocation"
    FOR EACH ROW EXECUTE FUNCTION fn_check_allocation_limits();

  -- Auto-update invoice status after allocation changes
  CREATE OR REPLACE FUNCTION fn_update_invoice_status() RETURNS trigger AS $$
  DECLARE
    total NUMERIC; paid NUMERIC; inv_id text;
  BEGIN
    inv_id := COALESCE(NEW.invoice, OLD.invoice);
    IF inv_id IS NULL THEN
      RETURN NULL;
    END IF;
    SELECT amount INTO total FROM tabInvoice WHERE name = inv_id FOR UPDATE;
    SELECT COALESCE(SUM(amount),0) INTO paid FROM "tabPayment Allocation" WHERE invoice = inv_id;

    IF total IS NULL THEN
      RETURN NULL;
    END IF;

    IF paid = 0 THEN
      UPDATE tabInvoice SET status='Sent' WHERE name = inv_id;
    ELSIF paid < total THEN
      UPDATE tabInvoice SET status='Paid' WHERE name = inv_id AND FALSE; -- keep as is; no partial state in current Invoice
      -- If you introduce a partial state, switch to: status='paid_part'
    ELSE
      UPDATE tabInvoice SET status='Paid' WHERE name = inv_id;
    END IF;
    RETURN NULL;
  END$$ LANGUAGE plpgsql;

  DROP TRIGGER IF EXISTS trg_alloc_after ON "tabPayment Allocation";
  CREATE TRIGGER trg_alloc_after
    AFTER INSERT OR UPDATE OR DELETE ON "tabPayment Allocation"
    FOR EACH ROW EXECUTE FUNCTION fn_update_invoice_status();
END$$;
