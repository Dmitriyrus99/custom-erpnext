frappe.listview_settings["Service Request"] = {
	get_indicator: function (doc) {
		const status = doc.status;
		const colors = {
			Open: "gray",
			"In Progress": "blue",
			Completed: "green",
			Closed: "dark",
			Cancelled: "red",
		};
		const color = colors[status] || "gray";
		return [__(status), color, "status,=," + status];
	},
	onload(listview) {
		listview.page.add_action_item(__("Create Service Report"), () => {
			const rows = listview.get_checked_items();
			if (rows.length !== 1) {
				frappe.msgprint({
					message: __("Please select exactly one row"),
					indicator: "orange",
				});
				return;
			}
			const row = rows[0];
			frappe.new_doc("Service Report", {
				service_request: row.name,
				report_date: frappe.datetime.get_today(),
			});
		});
	},
};
