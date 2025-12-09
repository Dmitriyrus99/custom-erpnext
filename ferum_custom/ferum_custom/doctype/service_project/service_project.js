frappe.ui.form.on("Service Project", {
	refresh(frm) {
		if (frm.is_new()) return;

		// Quick create invoices
		frm.add_custom_button(
			__("Customer Invoice"),
			() => {
				frappe.new_doc("Invoice", {
					project: frm.doc.name,
					counterparty_type: "Customer",
					counterparty_name: frm.doc.customer || "",
				});
			},
			__("Create")
		);

		frm.add_custom_button(
			__("Subcontractor Invoice"),
			() => {
				frappe.new_doc("Invoice", {
					project: frm.doc.name,
					counterparty_type: "Subcontractor",
				});
			},
			__("Create")
		);

		// Quick workflow actions
		const add_action = (label, action) => {
			frm.add_custom_button(
				__(label),
				async () => {
					try {
						await frappe.xcall("frappe.model.workflow.apply_action", {
							doctype: frm.doc.doctype,
							docname: frm.doc.name,
							action,
						});
						await frm.reload_doc();
						frappe.show_alert({
							message: __("Project status updated"),
							indicator: "green",
						});
					} catch (e) {
						frappe.msgprint({ message: e.message || e, indicator: "red" });
					}
				},
				__("Change Status")
			);
		};

		if (frm.doc.status === "Planned") add_action("Activate Project", "Activate");
		if (frm.doc.status === "Active") {
			add_action("Complete Project", "Complete");
			add_action("Cancel Project", "Cancel");
		}
		if (frm.doc.status === "Completed") add_action("Reopen Project", "Reopen");

		// Quick create Service Request tied to this project
		frm.add_custom_button(
			__("Issue"),
			() => {
				const objects = (frm.doc.objects || [])
					.map((row) => row.asset)
					.filter(Boolean);
				if (objects && objects.length) {
					const d = new frappe.ui.Dialog({
						title: __("Create Issue"),
						fields: [
							{
								fieldname: "service_object",
								fieldtype: "Select",
								label: __("Asset"),
								options: [""].concat(objects),
							},
							{
								fieldname: "title",
								fieldtype: "Data",
								label: __("Title"),
								default: frm.doc.project_name || __("New Issue"),
							},
						],
						primary_action_label: __("Create"),
						primary_action: (values) => {
							frappe.new_doc("Issue", {
								asset: values.service_object,
								subject: values.title,
							});
							d.hide();
						},
					});
					d.show();
				} else {
					frappe.new_doc("Issue", {
						subject: frm.doc.project_name || __("New Issue"),
					});
				}
			},
			__("Create")
		);
	},
});
