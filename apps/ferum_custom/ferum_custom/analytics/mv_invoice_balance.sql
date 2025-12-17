CREATE MATERIALIZED VIEW IF NOT EXISTS mv_invoice_balance AS
SELECT
  i.name                AS invoice_id,
  i.company             AS company_id,
  i.invoice_no,
  i.invoice_year,
  i.invoice_date,
  i.contract,
  i.project,
  i.customer,
  i.amount,
  COALESCE(SUM(pa.amount),0) AS paid_amount,
  GREATEST(i.amount - COALESCE(SUM(pa.amount),0), 0) AS due_amount,
  CASE
    WHEN i.status ILIKE 'cancelled' THEN 'cancelled'
    WHEN COALESCE(SUM(pa.amount),0) = 0 THEN 'sent'
    WHEN COALESCE(SUM(pa.amount),0) < i.amount THEN 'paid_part'
    ELSE 'paid'
  END AS computed_status
FROM tabInvoice i
LEFT JOIN "tabPayment Allocation" pa ON pa.invoice = i.name
GROUP BY i.name, i.company, i.invoice_no, i.invoice_year, i.invoice_date,
         i.contract, i.project, i.customer, i.amount, i.status;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_invoice_balance ON mv_invoice_balance(invoice_id);
