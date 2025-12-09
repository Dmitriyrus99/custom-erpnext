frappe.ui.form.on("Service Object", {
	refresh(frm) {
		if (frm.is_new()) return;
				frm.add_custom_button(
					__("Create Issue"),			() => {
				frappe.new_doc("Issue", {
					asset: frm.doc.name,
					subject: frm.doc.object_name || __("New Issue"),
				});
			},
			__("Create")
		);
	},
});
