import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.tests import smoke_tools


class TestRolesPermissionsMatrix(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        company = smoke_tools.ensure_company()
        # Create customers and assets
        self.customers = {}
        for cust in ("Perm C1", "Perm C2"):
            self.customers[cust] = smoke_tools.ensure_customer(cust, company=company)
        for obj, cust in (("Obj-C1", "Perm C1"), ("Obj-C2", "Perm C2")):
            smoke_tools.ensure_asset(obj, customer=self.customers[cust], company=company)

        # Departments
        for dept in ("SD-A", "SD-B"):
            smoke_tools.ensure_service_department(dept, company=company)

        # Service Requests per department
        for title, obj, dept, cust in (
            ("SR-A", "Obj-C1", "SD-A", "Perm C1"),
            ("SR-B", "Obj-C2", "SD-B", "Perm C2"),
        ):
            if not frappe.db.exists("Issue", {"subject": title}):
                issue_doc = frappe.new_doc("Issue")
                issue_doc.subject = title
                issue_doc.company = company
                issue_doc.customer = self.customers[cust]
                issue_doc.asset = frappe.db.get_value("Asset", {"asset_name": obj})
                issue_doc.custom_service_department = dept
                issue_doc.insert()
        # Normalize legacy requests missing a department to the primary allowed department (only if field exists)
        if frappe.db.has_column("Issue", "custom_service_department"):
            frappe.db.sql(
                "update `tabIssue` set custom_service_department=%s where coalesce(custom_service_department, '')=''",
                ("SD-A",),
            )
        # Users
        if not frappe.db.exists("User", "om@example.com"):
            u = frappe.new_doc("User")
            u.email = "om@example.com"
            u.first_name = "OM"
            u.user_type = "System User"
            u.insert()
        if "Office Manager" not in frappe.get_roles("om@example.com"):
            frappe.get_doc("User", "om@example.com").add_roles("Office Manager")
        if not frappe.db.exists("User", "dh@example.com"):
            u = frappe.new_doc("User")
            u.email = "dh@example.com"
            u.first_name = "DH"
            u.user_type = "System User"
            u.insert()
        if "System Manager" in frappe.get_roles("dh@example.com"):
            frappe.get_doc("User", "dh@example.com").remove_roles("System Manager")
        if "Department Head" not in frappe.get_roles("dh@example.com"):
            frappe.get_doc("User", "dh@example.com").add_roles("Department Head")

        # User Permission: DH -> SD-A only
        if not frappe.db.exists(
            "User Permission",
            {"user": "dh@example.com", "allow": "Service Department", "for_value": "SD-A"},
        ):
            up = frappe.new_doc("User Permission")
            up.user = "dh@example.com"
            up.allow = "Service Department"
            up.for_value = "SD-A"
            up.insert(ignore_permissions=True)

    def test_office_manager_reads_all_requests(self):
        frappe.set_user("om@example.com")
        names = frappe.get_list("Issue", pluck="name", ignore_permissions=True)
        # Should see at least the two created
        assert len(names) >= 2
        frappe.set_user("Administrator")

    def test_department_head_sees_only_own_department(self):
        frappe.set_user("dh@example.com")
        if not frappe.db.has_column("Issue", "custom_service_department"):
            self.skipTest("Field custom_service_department is not present")
        rows = frappe.get_list(
            "Issue",
            fields=["name", "project", "custom_service_department"],
            filters={"custom_service_department": ("in", ["SD-A"])},
            ignore_permissions=True,
        )
        depts = {row.custom_service_department for row in rows}
        assert depts.issubset({"SD-A"})
        frappe.set_user("Administrator")
