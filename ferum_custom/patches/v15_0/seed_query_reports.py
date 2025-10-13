from __future__ import annotations

import frappe


def _upsert_report(name: str, ref_doctype: str, query: str) -> None:
    doc = frappe.db.exists("Report", name)
    if doc:
        report = frappe.get_doc("Report", name)
        report.module = "Ferum Custom"
        report.report_type = "Query Report"
        report.is_standard = "Yes"
        report.ref_doctype = ref_doctype
        report.query = query
        report.save(ignore_permissions=True)
    else:
        report = frappe.get_doc(
            {
                "doctype": "Report",
                "report_name": name,
                "module": "Ferum Custom",
                "is_standard": "Yes",
                "ref_doctype": ref_doctype,
                "report_type": "Query Report",
                "query": query,
            }
        )
        report.insert(ignore_permissions=True)


def execute():
    _upsert_report(
        "Unassigned Issues",
        "Issue",
        """SELECT i.name, i.subject, i.status, i.priority, i.project, i.customer, i.modified
        FROM `tabIssue` i
        LEFT JOIN `tabToDo` t ON t.reference_type='Issue' AND t.reference_name=i.name AND t.status='Open'
        WHERE i.status NOT IN ('Closed','Resolved') AND t.name IS NULL
        ORDER BY i.modified DESC""",
    )

    _upsert_report(
        "Open Issues by Engineer",
        "Issue",
        """SELECT t.allocated_to AS engineer, COUNT(*) AS open_issues
        FROM `tabToDo` t
        JOIN `tabIssue` i ON i.name=t.reference_name AND t.reference_type='Issue'
        WHERE t.status='Open' AND i.status NOT IN ('Closed','Resolved')
        GROUP BY t.allocated_to
        ORDER BY open_issues DESC""",
    )

    _upsert_report(
        "Engineer Utilization (30d)",
        "Timesheet",
        """SELECT ts.employee AS employee, SUM(w.hours) AS hours
        FROM `tabTimesheet` ts
        JOIN `tabTimesheet Detail` w ON w.parent = ts.name
        WHERE ts.docstatus = 1 AND ts.start_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY ts.employee
        ORDER BY hours DESC""",
    )

    _upsert_report(
        "Project Profitability (Simple)",
        "Project",
        """SELECT p.name AS project,
        COALESCE(SUM(si.grand_total),0) AS income,
        COALESCE(SUM(pi.grand_total),0) AS expense,
        COALESCE(SUM(si.grand_total),0)-COALESCE(SUM(pi.grand_total),0) AS profit
        FROM `tabProject` p
        LEFT JOIN `tabSales Invoice` si ON si.project=p.name AND si.docstatus=1
        LEFT JOIN `tabPurchase Invoice` pi ON pi.project=p.name AND pi.docstatus=1
        GROUP BY p.name
        ORDER BY profit DESC""",
    )

