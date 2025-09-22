import frappe


def execute():
    # Unique pair (parent, service_object) on child table Project Object Item
    try:
        frappe.db.sql(
            """
            ALTER TABLE `tabProject Object Item`
            ADD UNIQUE KEY IF NOT EXISTS `uniq_parent_object` (`parent`, `service_object`)
            """
        )
    except Exception:
        # MariaDB before 10.5 doesn't support IF NOT EXISTS on add unique, try fallback
        try:
            # create only if not present
            idx = frappe.db.sql(
                """SHOW INDEX FROM `tabProject Object Item` WHERE Key_name='uniq_parent_object'"""
            )
            if not idx:
                frappe.db.sql(
                    """ALTER TABLE `tabProject Object Item` ADD UNIQUE KEY `uniq_parent_object` (`parent`, `service_object`)"""
                )
        except Exception:
            pass

    # Helpful filters indexes
    _add_index("Service Request", "idx_sr_project_status_assigned", ["project", "status", "assigned_to"])
    _add_index("Service Report", "idx_srp_request_status", ["service_request", "status"])
    _add_index("Invoice", "idx_inv_project_status", ["project", "status"]) 


def _add_index(doctype: str, name: str, fields: list[str]):
    cols = ",".join(f"`{f}`" for f in fields)
    try:
        frappe.db.sql(f"CREATE INDEX `{name}` ON `tab{doctype}` ({cols})")
    except Exception:
        pass

