frappe.ui.form.on("Service Report", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Create Sales Invoice"), async () => {
			try {
				const r = await frappe.call({
					method: "ferum_custom.ferum_custom.doctype.service_report.service_report.create_sales_invoice_from_report",
					args: { service_report: frm.doc.name },
				});
				if (r.message) {
					frappe.msgprint(__("Sales Invoice {0} created", [r.message]));
					frm.reload_doc();
				}
			} catch (e) {
				console.error(e);
			}
		});
	},
});
