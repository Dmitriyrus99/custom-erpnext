frappe.listview_settings["Invoice"] = {
	onload(listview) {
		listview.page.add_actions_menu_item(__("Mark Sent"), async () => {
			const names = listview.get_checked_items().map((d) => d.name);
			if (!names.length) return;
			try {
				const r = await frappe.call({
					method: "ferum_custom.ferum_custom.doctype.invoice.invoice.bulk_mark_sent",
					args: { names },
				});
				frappe.show_alert({
					message: __("Updated: {0}, Skipped: {1}").format(
						(r.message && r.message.updated && r.message.updated.length) || 0,
						(r.message && r.message.skipped && r.message.skipped.length) || 0
					),
					indicator: "green",
				});
				listview.refresh();
			} catch (e) {
				frappe.msgprint({ message: e.message || e, indicator: "red" });
			}
		});

		listview.page.add_actions_menu_item(__("Mark Paid"), async () => {
			const names = listview.get_checked_items().map((d) => d.name);
			if (!names.length) return;
			try {
				const r = await frappe.call({
					method: "ferum_custom.ferum_custom.doctype.invoice.invoice.bulk_mark_paid",
					args: { names },
				});
				frappe.show_alert({
					message: __("Updated: {0}, Skipped: {1}").format(
						(r.message && r.message.updated && r.message.updated.length) || 0,
						(r.message && r.message.skipped && r.message.skipped.length) || 0
					),
					indicator: "green",
				});
				listview.refresh();
			} catch (e) {
				frappe.msgprint({ message: e.message || e, indicator: "red" });
			}
		});
	},
};
