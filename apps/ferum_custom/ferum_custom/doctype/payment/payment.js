frappe.ui.form.on("Payment", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Create Payment Entry"), async () => {
			if (!frm.doc.customer && !frm.doc.counterparty) {
				frappe.msgprint(__("Set Customer or Counterparty before export."));
				return;
			}
			try {
				const pe = await frappe.call({
					method: "ferum_custom.ferum_custom.doctype.payment.payment.create_payment_entry_from_payment",
					args: { payment_name: frm.doc.name },
				});
				if (pe && pe.message) {
					frappe.msgprint(__("Payment Entry {0} created", [pe.message]));
					frm.reload_doc();
				}
			} catch (e) {
				// Errors are already raised server-side
				frappe.msgprint(__("Could not create Payment Entry. Please try again."));
			}
		});
	},
});
