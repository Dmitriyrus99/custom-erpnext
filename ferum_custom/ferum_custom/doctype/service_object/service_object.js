frappe.ui.form.on("Service Object", {
	refresh(frm) {
		if (frm.is_new()) return;
		frm.add_custom_button(
			__("Create Service Request"),
			() => {
				frappe.new_doc("Service Request", {
					service_object: frm.doc.name,
					title: frm.doc.object_name || __("Service Request"),
				});
			},
			__("Create"),
		);
	},
});
