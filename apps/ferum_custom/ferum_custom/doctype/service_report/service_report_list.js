frappe.listview_settings["Service Report"] = {
	get_indicator: function (doc) {
		const status = doc.status;
		const colors = {
			Draft: "gray",
			Submitted: "blue",
			Approved: "green",
			Archived: "dark",
			Cancelled: "red",
		};
		const color = colors[status] || "gray";
		return [__(status), color, "status,=," + status];
	},
};
