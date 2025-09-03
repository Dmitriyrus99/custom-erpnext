frappe.ui.form.on("Service Report", {
	refresh(frm) {
		if (frm.is_new()) return;
		// Allow creating invoices from approved report (safer UX)
		if (frm.doc.status === "Approved") {
			frm.add_custom_button(
				__("Customer Invoice"),
				() => {
					if (!frm.doc.service_request) {
						frappe.new_doc("Invoice", { counterparty_type: "Customer", amount: frm.doc.total_amount });
						return;
					}
					frappe.db
						.get_value("Service Request", frm.doc.service_request, ["project", "customer"])
						.then((r) => {
							const project = r?.message?.project;
							const customer = r?.message?.customer;
							frappe.new_doc("Invoice", {
								project,
								counterparty_type: "Customer",
								counterparty_name: customer,
								amount: frm.doc.total_amount,
							});
						});
				},
				__("Create"),
			);
			frm.add_custom_button(
				__("Subcontractor Invoice"),
				() => {
					if (!frm.doc.service_request) {
						frappe.new_doc("Invoice", { counterparty_type: "Subcontractor" });
						return;
					}
					frappe.db
						.get_value("Service Request", frm.doc.service_request, "project")
						.then((r) => {
							const project = r && r.message ? r.message.project : undefined;
							frappe.new_doc("Invoice", {
								project,
								counterparty_type: "Subcontractor",
							});
						});
				},
				__("Create"),
			);
		}
	},
});
