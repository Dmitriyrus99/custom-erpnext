CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cashflow_daily AS
SELECT
  p.company AS company_id,
  p.trx_date::date AS date,
  SUM(p.amount) FILTER (WHERE p.direction='in')  AS incoming,
  SUM(p.amount) FILTER (WHERE p.direction='out') AS outgoing,
  COALESCE(SUM(p.amount) FILTER (WHERE p.direction='in'),0)
  - COALESCE(SUM(p.amount) FILTER (WHERE p.direction='out'),0) AS netto
FROM tabPayment p
GROUP BY p.company, p.trx_date::date;

CREATE INDEX IF NOT EXISTS idx_mv_cashflow_daily ON mv_cashflow_daily(company_id, date);
