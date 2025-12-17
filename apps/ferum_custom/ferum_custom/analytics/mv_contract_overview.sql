CREATE MATERIALIZED VIEW IF NOT EXISTS mv_contract_overview AS
SELECT
  c.name AS contract_id,
  c.company AS company_id,
  c.customer,
  c.project,
  c.amount_max,
  COALESCE(SUM(i.amount),0) AS invoiced_total,
  COALESCE(SUM(b.paid_amount),0) AS paid_total,
  GREATEST(COALESCE(SUM(i.amount),0) - COALESCE(SUM(b.paid_amount),0), 0) AS outstanding,
  CASE
    WHEN c.amount_max IS NULL OR c.amount_max = 0 THEN NULL
    ELSE ROUND(100.0 * COALESCE(SUM(i.amount),0) / c.amount_max, 2)
  END AS limit_used_percent,
  GREATEST(COALESCE(SUM(i.amount),0) - COALESCE(c.amount_max,0), 0) AS overlimit_amount
FROM tabContract c
LEFT JOIN tabInvoice i ON i.contract = c.name
LEFT JOIN mv_invoice_balance b ON b.invoice_id = i.name
GROUP BY c.name, c.company, c.customer, c.project, c.amount_max;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_contract_overview ON mv_contract_overview(contract_id);
