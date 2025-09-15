frappe.listview_settings["Invoice"] = {
	onload(listview) {
		// Quick filters by Type
		listview.page.add_inner_button(
			__("Customer"),
			() => {
				listview.filter_area.clear();
				listview.filter_area.add([["Invoice", "counterparty_type", "=", "Customer"]]);
				listview.refresh();
			},
			__("Type")
		);

		listview.page.add_inner_button(
			__("Subcontractor"),
			() => {
				listview.filter_area.clear();
				listview.filter_area.add([["Invoice", "counterparty_type", "=", "Subcontractor"]]);
				listview.refresh();
			},
			__("Type")
		);

		// Quick filters by Status
		["Draft", "Sent", "Paid"].forEach((status) => {
			listview.page.add_inner_button(
				__(status),
				() => {
					listview.filter_area.clear();
					listview.filter_area.add([["Invoice", "status", "=", status]]);
					listview.refresh();
				},
				__("Status")
			);
		});

		// Bulk action: Mark as Sent (role-gated)
		const can_mark_sent = [
			"System Manager",
			"Project Manager",
			"Office Manager",
			"Chief Accountant",
		].some((r) => frappe.user.has_role(r));

		if (can_mark_sent)
			listview.page.add_actions_menu_item(__("Mark as Sent"), async () => {
				const selected = listview.get_checked_items();
				if (!selected.length) {
					frappe.msgprint({
						message: __("Select at least one invoice."),
						indicator: "orange",
					});
					return;
				}
				const names = selected.map((d) => d.name);
				try {
					const r = await frappe.call({
						method: "ferum_custom.ferum_custom.doctype.invoice.invoice.bulk_mark_sent",
						args: { names },
					});
					const msg = r.message || {};
					const updated = (msg.updated || []).length;
					const skipped = (msg.skipped || []).length;
					frappe.show_alert({
						message: __("Updated: {0}, Skipped: {1}").format(updated, skipped),
						indicator: updated ? "green" : "orange",
					});
				} catch (e) {
					frappe.msgprint({ message: e.message || e, indicator: "red" });
				} finally {
					listview.refresh();
				}
			});

		// Bulk action: Mark as Paid (Chief Accountant only)
		const can_mark_paid = ["Chief Accountant", "System Manager"].some((r) =>
			frappe.user.has_role(r)
		);
		if (can_mark_paid)
			listview.page.add_actions_menu_item(__("Mark as Paid"), async () => {
				const selected = listview.get_checked_items();
				if (!selected.length) {
					frappe.msgprint({
						message: __("Select at least one invoice."),
						indicator: "orange",
					});
					return;
				}
				const names = selected.map((d) => d.name);
				try {
					const r = await frappe.call({
						method: "ferum_custom.ferum_custom.doctype.invoice.invoice.bulk_mark_paid",
						args: { names },
					});
					const msg = r.message || {};
					const updated = (msg.updated || []).length;
					const skipped = (msg.skipped || []).length;
					frappe.show_alert({
						message: __("Marked Paid: {0}, Skipped: {1}").format(updated, skipped),
						indicator: updated ? "green" : "orange",
					});
				} catch (e) {
					frappe.msgprint({ message: e.message || e, indicator: "red" });
				} finally {
					listview.refresh();
				}
			});
	},

	get_indicator(doc) {
		const status = doc.status;
		const colors = { Draft: "gray", Sent: "blue", Paid: "green", Cancelled: "red" };
		const color = colors[status] || "gray";
		return [__(status), color, "status,=," + status];
	},
};
