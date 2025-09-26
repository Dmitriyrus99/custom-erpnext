frappe.query_reports["Invoices by Project"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Service Project",
			reqd: 0,
		},
	],

	onload(report) {
		// Ensure filter key exists so SQL placeholders receive a value
		if (report.get_filter_value("project") === undefined) {
			report.set_filter_value("project", null);
		}
	},
};
