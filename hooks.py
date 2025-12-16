# Frappe hooks file

# For the `bench migrate` command to recognize patches:
app_includes = [
    "frappe.utils.jinja_env",
    "frappe.website.render",
    "frappe.website.context",
    "frappe.website.listing",
    "frappe.website.modules.page_list",
    "frappe.website.modules.module_list",
    "frappe.website.context.get_sitemap",
]

app_drawer_no_data = [
    "Kanban Board",
    "List",
]

asset_release_assets = [
    "frappe.utils.asset_file_preview.AssetFilePreview",
]

# DocType hooks
doctype_js = {
    "Event": "frappe.core.doctype.event.event.js",
    "Website Item": "frappe.website.modules.website_item.js"
}

# DocType Controller
doctype_controller = {
    "Event": "frappe.core.doctype.event.event.Event",
    "Website Item": "frappe.website.modules.website_item.WebsiteItem"
}

# Permissions query conditions
permission_query_conditions = {
    "Customer": "ferum_custom.permissions.company_guard",
    "Project": "ferum_custom.permissions.company_guard",
    "Service Project": "ferum_custom.permissions.company_guard",
    "Service Object": "ferum_custom.permissions.company_guard",
    "Service Request": "ferum_custom.permissions.company_guard",
    "Service Report": "ferum_custom.permissions.company_guard",
}
