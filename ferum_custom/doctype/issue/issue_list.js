frappe.listview_settings["Issue"] = {
	add_fields: ["status", "priority", "assigned_engineer", "project", "modified", "subject"],

	get_indicator(doc) {
		const colors = {
			Open: "red",
			"In Progress": "blue",
			Resolved: "green",
			Closed: "dark",
		};
		const status = doc.status || "Open";
		return [__(status), colors[status] || "gray", `status,=,${status}`];
	},

	onload(listview) {
		const doctype = listview.doctype;
		const apply = (filters) =>
			listview.filter_area.clear().then(() => listview.filter_area.add(filters));

		// Quick filters: Status
		[
			["Open", [[doctype, "status", "=", "Open"]]],
			["In Progress", [[doctype, "status", "=", "In Progress"]]],
			["Resolved", [[doctype, "status", "=", "Resolved"]]],
			["Closed", [[doctype, "status", "=", "Closed"]]],
		].forEach(([label, flt]) =>
			listview.page.add_inner_button(__(label), () => apply(flt), __("Status"))
		);

		// Quick filters: Assignment
		const user = frappe.session.user;
		listview.page.add_inner_button(
			__("Assigned to Me"),
			() =>
				apply([
					[doctype, "assigned_engineer", "=", user],
					[doctype, "status", "!=", "Closed"],
				]),
			__("Assigned")
		);
		listview.page.add_inner_button(__("All"), () => apply([]), __("Assigned"));

		// Quick filters: Project
		listview.page.add_inner_button(
			__("By Project"),
			() => {
				frappe.prompt(
					[
						{
							label: __("Project"),
							fieldname: "project",
							fieldtype: "Link",
							options: "Project",
							reqd: 1,
						},
					],
					(v) => apply([[doctype, "project", "=", v.project]])
				);
			},
			__("Project")
		);

		// Role-aware default filters (apply only when no filters yet)
		const has_no_filters = !(listview.filter_area.get() || []).length;
		if (has_no_filters) {
			if (frappe.user.has_role("Service Engineer")) {
				apply([
					[doctype, "assigned_engineer", "=", user],
					[doctype, "status", "!=", "Closed"],
				]);
			} else if (frappe.user.has_role("Project Manager")) {
				frappe
					.call({
						method: "ferum_custom.ferum_custom.api.listview.get_projects_for_pm",
						args: { user, doctype: "Project" },
					})
					.then((r) => {
						const projects = (r && r.message) || [];
						const filters = [[doctype, "status", "!=", "Closed"]];
						if (projects.length) filters.push([doctype, "project", "in", projects]);
						apply(filters);
					});
			}
		}
	},
};
