frappe.listview_settings["Service Object"] = {
	onload(listview) {
		listview.page.add_inner_button(__("Create Service Request"), () => {
			const selected = listview.get_checked_items();
			if (selected.length !== 1) {
				frappe.msgprint({
					message: __("Please select exactly one Service Object."),
					indicator: "orange",
				});
				return;
			}
			const obj = selected[0];
			frappe.new_doc("Service Request", {
				service_object: obj.name,
				title: obj.object_name || __("Service Request"),
			});
		});
	},
};
