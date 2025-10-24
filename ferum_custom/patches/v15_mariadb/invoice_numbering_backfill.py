import frappe


def execute():
    """Backfill invoice_year and invoice_no with safe defaults.

    - year from invoice_date if present; otherwise current year
    - no from name if missing
    """
    # year
    frappe.db.sql(
        """
        UPDATE `tabInvoice`
        SET invoice_year = YEAR(invoice_date)
        WHERE (invoice_year IS NULL OR invoice_year = 0)
          AND invoice_date IS NOT NULL
        """
    )
    # default when invoice_date missing: use YEAR(CURDATE())
    frappe.db.sql(
        """
        UPDATE `tabInvoice`
        SET invoice_year = YEAR(CURDATE())
        WHERE (invoice_year IS NULL OR invoice_year = 0)
        """
    )
    # number: fallback to name
    frappe.db.sql(
        """
        UPDATE `tabInvoice`
        SET invoice_no = LEFT(name, 140)
        WHERE (invoice_no IS NULL OR invoice_no = '')
        """
    )

