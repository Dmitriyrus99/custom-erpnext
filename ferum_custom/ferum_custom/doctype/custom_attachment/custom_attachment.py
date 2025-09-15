import frappe
from frappe.model.document import Document


def _pgc_for_custom_attachment(user: str) -> str:
    roles = set(frappe.get_roles(user))
    if "System Manager" in roles:
        return None  # no restriction

    conds: list[str] = []
    # Project Manager: attachments linked to Service Reports under their projects
    if "Project Manager" in roles:
        conds.append(
            "exists("
            " select 1 from `tabService Report Document Item` srd"
            " join `tabService Report` sr on sr.name=srd.parent"
            " join `tabService Request` req on req.name=sr.service_request"
            " join `tabService Project` sp on sp.name=req.project"
            " where srd.custom_attachment=`tabCustom Attachment`.name"
            " and sp.project_manager=%(user)s)"
        )
    # Service Engineer: attachments through requests assigned to user
    if "Service Engineer" in roles:
        conds.append(
            "exists("
            " select 1 from `tabService Report Document Item` srd"
            " join `tabService Report` sr on sr.name=srd.parent"
            " join `tabService Request` req on req.name=sr.service_request"
            " where srd.custom_attachment=`tabCustom Attachment`.name"
            " and req.assigned_to=%(user)s)"
        )
    # Client: attachments via requests owned by user
    if "Client" in roles:
        conds.append(
            "exists("
            " select 1 from `tabService Report Document Item` srd"
            " join `tabService Report` sr on sr.name=srd.parent"
            " join `tabService Request` req on req.name=sr.service_request"
            " where srd.custom_attachment=`tabCustom Attachment`.name"
            " and req.owner=%(user)s)"
        )
    # Office Manager / Chief Accountant: broad read access
    if "Office Manager" in roles or "Chief Accountant" in roles:
        # No extra filters for these roles
        return None

    if not conds:
        return "1=0"
    return "(" + ") or (".join(conds) + ")"


def get_permission_query_conditions(user: str | None = None) -> str | None:
    user = user or frappe.session.user
    return _pgc_for_custom_attachment(user)


def has_permission(doc, user: str | None = None) -> bool:
    user = user or frappe.session.user
    roles = set(frappe.get_roles(user))
    if "System Manager" in roles:
        return True
    if "Office Manager" in roles:
        return True
    if "Chief Accountant" in roles:
        return True
    if doc.owner == user:
        return True
    # Project Manager: via project manager of linked Service Report -> Service Request
    if "Project Manager" in roles:
        pm = frappe.db.sql(
            """
        select sp.project_manager
        from `tabService Report Document Item` srd
        join `tabService Report` sr on sr.name = srd.parent
        join `tabService Request` req on req.name = sr.service_request
        join `tabService Project` sp on sp.name = req.project
        where srd.custom_attachment=%s limit 1
        """,
            (doc.name,),
        )
        if pm and pm[0][0] == user:
            return True
    # Service Engineer: assignee of parent request
    if "Service Engineer" in roles:
        assignee = frappe.db.sql(
            """
        select req.assigned_to
        from `tabService Report Document Item` srd
        join `tabService Report` sr on sr.name = srd.parent
        join `tabService Request` req on req.name = sr.service_request
        where srd.custom_attachment=%s limit 1
        """,
            (doc.name,),
        )
        if assignee and assignee[0][0] == user:
            return True
    # Client: owner of parent request
    if "Client" in roles:
        owner = frappe.db.sql(
            """
        select req.owner
        from `tabService Report Document Item` srd
        join `tabService Report` sr on sr.name = srd.parent
        join `tabService Request` req on req.name = sr.service_request
        where srd.custom_attachment=%s limit 1
        """,
            (doc.name,),
        )
        if owner and owner[0][0] == user:
            return True
    return False


class CustomAttachment(Document):
    # Google Drive sync removed by request. No background syncing is performed.
    pass
