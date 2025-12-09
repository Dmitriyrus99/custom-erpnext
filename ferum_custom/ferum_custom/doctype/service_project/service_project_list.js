frappe.listview_settings["Service Project"] = {
	get_indicator: function (doc) {
		const status = doc.status;
		const colors = {
			Planned: "gray",
			Active: "blue",
			Completed: "green",
			Cancelled: "red",
		};
		const color = colors[status] || "gray";
		return [__(status), color, "status,=," + status];
	},
	onload(listview) {
		function ensure_one() {
			const rows = listview.get_checked_items();
			if (rows.length !== 1) {
				frappe.msgprint({
					message: __("Please select exactly one row"),
					indicator: "orange",
				});
				return null;
			}
			return rows[0];
		}

		listview.page.add_action_item(__("Create Customer Invoice"), () => {
			const row = ensure_one();
			if (!row) return;
			frappe.new_doc("Invoice", {
				project: row.name,
				counterparty_type: "Customer",
			});
		});

		listview.page.add_action_item(__("Create Subcontractor Invoice"), () => {
			const row = ensure_one();
			if (!row) return;
			frappe.new_doc("Invoice", {
				project: row.name,
				counterparty_type: "Subcontractor",
			});
		});

		function apply_action(action) {
			const row = ensure_one();
			if (!row) return;
			frappe.call({
				method: "frappe.model.workflow.apply_action",
				args: { doctype: "Service Project", docname: row.name, action },
				callback: () => listview.refresh(),
				error: (e) => frappe.msgprint({ message: e.message, indicator: "red" }),
			});
		}

		listview.page.add_action_item(__("Activate Project"), () => apply_action("Activate"));
		listview.page.add_action_item(__("Complete Project"), () => apply_action("Complete"));
		listview.page.add_action_item(__("Cancel Project"), () => apply_action("Cancel"));
		listview.page.add_action_item(__("Reopen Project"), () => apply_action("Reopen"));

		// Create Service Request from selected project (prompts for Service Object if available)
		listview.page.add_action_item(__("Create Issue"), async () => {
			const row = ensure_one();
			if (!row) return;
			try {
				const project = await frappe.db.get_doc("Project", row.name);
				const objects = (project.objects || [])
					.map((o) => o.service_object)
					.filter(Boolean);
				if (objects.length) {
					const d = new frappe.ui.Dialog({
						title: __("Create Issue"),
						fields: [
							{
								fieldname: "service_object",
								fieldtype: "Select",
								label: __("Asset"),
								options: [""].concat(objects.map((o) => o.asset)).filter(Boolean),
							},
							{
								fieldname: "title",
								fieldtype: "Data",
								label: __("Title"),
								default: project.project_name || __("New Issue"),
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
						subject: project.project_name || __("New Issue"),
					});
				}
			} catch (e) {
				frappe.msgprint({ message: e.message || e, indicator: "red" });
			}
		});
	},
};
