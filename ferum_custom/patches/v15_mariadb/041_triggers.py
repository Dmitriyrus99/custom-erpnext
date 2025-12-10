import frappe


def _drop_and_create(trigger_name: str, create_ddl: str) -> None:
	"""Replace the trigger so rerunning the patch is safe."""
	frappe.db.sql(f"DROP TRIGGER IF EXISTS {trigger_name}")
	frappe.db.sql(create_ddl)


def execute():
	_drop_and_create(
		"trg_check_allocation_limits",
		"""
        CREATE TRIGGER trg_check_allocation_limits
        BEFORE INSERT ON `tabPayment Allocation`
        FOR EACH ROW
        BEGIN
          DECLARE inv_total DECIMAL(18,2);
          DECLARE inv_sum DECIMAL(18,2);
          DECLARE pay_total DECIMAL(18,2);
          DECLARE pay_sum DECIMAL(18,2);

          SELECT amount INTO inv_total
            FROM `tabInvoice`
            WHERE name = NEW.invoice;

          SELECT IFNULL(SUM(amount), 0)
            INTO inv_sum
            FROM `tabPayment Allocation`
            WHERE invoice = NEW.invoice;

          IF inv_sum + NEW.amount > inv_total THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Allocation exceeds invoice total';
          END IF;

          SELECT amount INTO pay_total
            FROM `tabPayment`
            WHERE name = NEW.payment;

          SELECT IFNULL(SUM(amount), 0)
            INTO pay_sum
            FROM `tabPayment Allocation`
            WHERE payment = NEW.payment;

          IF pay_sum + NEW.amount > pay_total THEN
            SIGNAL SQLSTATE '45000'
              SET MESSAGE_TEXT = 'Allocation exceeds payment total';
          END IF;
        END
        """,
	)

	_drop_and_create(
		"trg_update_invoice_status",
		"""
        CREATE TRIGGER trg_update_invoice_status
        AFTER INSERT ON `tabPayment Allocation`
        FOR EACH ROW
        BEGIN
          DECLARE total DECIMAL(18,2);
          DECLARE paid DECIMAL(18,2);

          SELECT amount INTO total
            FROM `tabInvoice`
            WHERE name = NEW.invoice;

          SELECT IFNULL(SUM(amount), 0)
            INTO paid
            FROM `tabPayment Allocation`
            WHERE invoice = NEW.invoice;

          IF paid = 0 THEN
            UPDATE `tabInvoice`
              SET status = 'sent'
              WHERE name = NEW.invoice;
          ELSEIF paid < total THEN
            UPDATE `tabInvoice`
              SET status = 'paid_part'
              WHERE name = NEW.invoice;
          ELSE
            UPDATE `tabInvoice`
              SET status = 'paid'
              WHERE name = NEW.invoice;
          END IF;
        END
        """,
	)

	_drop_and_create(
		"trg_after_report_insert",
		"""
        CREATE TRIGGER trg_after_report_insert
        AFTER INSERT ON `tabService Report`
        FOR EACH ROW
        BEGIN
          UPDATE `tabService Request`
            SET status = 'Completed',
                actual_end_datetime = IFNULL(actual_end_datetime, NOW()),
                linked_report = NEW.name
            WHERE name = NEW.service_request
              AND status NOT IN ('Completed', 'Closed');
        END
        """,
	)
