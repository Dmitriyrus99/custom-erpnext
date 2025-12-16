import frappe

def company_guard(user):
    if frappe.session.user == "Administrator":
        return ""

    companies = frappe.get_all(
        "User Permission",
        filters={
            "user": frappe.session.user,
            "allow": "Company",
        },
        pluck="for_value",
    )

    if not companies:
        return "1=0"  # Deny access if no company permissions are found

    # Ensure companies are properly quoted for SQL
    escaped_companies = [frappe.db.escape(c) for c in companies]
    
    return f"`tab{{doctype}}`.company in ({', '.join(escaped_companies)})"