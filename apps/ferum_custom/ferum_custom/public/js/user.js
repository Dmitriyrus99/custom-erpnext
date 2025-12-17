frappe.ui.form.on("User", {
	async validate(frm) {
		await ensure_user_type_matches_roles(frm);
	},
});

async function ensure_user_type_matches_roles(frm) {
	try {
		const role_names = (frm.doc.roles || []).map((r) => r.role).filter(Boolean);
		if (!role_names.length) return;

		const roles = await frappe.db.get_list("Role", {
			fields: ["name", "desk_access"],
			filters: { name: ["in", role_names] },
			limit: role_names.length,
		});

		const has_desk_role = roles.some((r) => r.desk_access);
		const desired_type = has_desk_role ? "System User" : "Website User";

		if (frm.doc.user_type !== desired_type) {
			await frm.set_value("user_type", desired_type);
			frappe.show_alert({
				message: __("User Type set to: {0}").format(desired_type),
				indicator: "blue",
			});
		}
	} catch (e) {
		// graceful degradation; server-side validation still applies
	}
}
