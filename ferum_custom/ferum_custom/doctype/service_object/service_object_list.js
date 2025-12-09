frappe.listview_settings["Service Object"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Create Issue"), () => {
			const selected = listview.get_checked_items();
			if (selected.length !== 1) {
									frappe.msgprint({
										message: __("Please select exactly one Asset."),					indicator: "orange",
				});
				return;
			}
			const obj = selected[0];
							frappe.new_doc("Issue", {
								asset: obj.name,
								subject: obj.object_name || __("New Issue"),
							});		});
	},
};
