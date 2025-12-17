CREATE OR REPLACE VIEW `vw_invoice_balance` AS
SELECT
  i.name AS invoice_id,
  i.company,
  i.invoice_no,
  i.invoice_year,
  i.invoice_date,
  i.contract,
  i.project,
  i.customer,
  i.amount,
  IFNULL(SUM(a.amount),0) AS paid_amount,
  GREATEST(i.amount - IFNULL(SUM(a.amount),0),0) AS due_amount,
  CASE
    WHEN i.status='cancelled' THEN 'cancelled'
    WHEN IFNULL(SUM(a.amount),0)=0 THEN 'sent'
    WHEN IFNULL(SUM(a.amount),0)<i.amount THEN 'paid_part'
    ELSE 'paid'
  END AS computed_status
FROM `tabInvoice` i
LEFT JOIN `tabPayment Allocation` a ON a.invoice=i.name
GROUP BY i.name;

CREATE OR REPLACE VIEW `vw_contract_overview` AS
SELECT
  c.name AS contract_id,
  c.company,
  c.customer,
  c.project,
  c.amount_max,
  IFNULL(SUM(i.amount),0) AS invoiced_total,
  IFNULL(SUM(ab.paid_amount),0) AS paid_total,
  GREATEST(IFNULL(SUM(i.amount),0)-IFNULL(SUM(ab.paid_amount),0),0) AS outstanding
FROM `tabContract` c
LEFT JOIN `tabInvoice` i ON i.contract=c.name
LEFT JOIN `vw_invoice_balance` ab ON ab.invoice_id=i.name
GROUP BY c.name;

CREATE OR REPLACE VIEW `vw_cashflow_daily` AS
SELECT
  p.company,
  DATE(p.trx_date) AS date,
  SUM(CASE WHEN p.direction='in' THEN p.amount ELSE 0 END) AS incoming,
  SUM(CASE WHEN p.direction='out' THEN p.amount ELSE 0 END) AS outgoing,
  SUM(CASE WHEN p.direction='in' THEN p.amount ELSE 0 END) -
  SUM(CASE WHEN p.direction='out' THEN p.amount ELSE 0 END) AS netto
FROM `tabPayment` p
GROUP BY p.company, DATE(p.trx_date);

-- Optional: schedule refresh using EVENT
CREATE EVENT IF NOT EXISTS ev_refresh_views
ON SCHEDULE EVERY 1 DAY
DO
  CALL sys.ps_truncate_statement_digest(); -- or custom refresh logic placeholder
