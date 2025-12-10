frappe.ui.form.on("Service Request", {
	refresh: function (frm) {
		if (!frm.is_new() && frm.doc.status !== "Closed") {
			frm.add_custom_button(
				__("Create Service Report"),
				function () {
					frappe.new_doc("Service Report", {
						service_request: frm.doc.name,
						report_date: frappe.datetime.get_today(),
					});
				},
				__("Create")
			);
		}
	},
	service_object: function (frm) {
		if (frm.doc.service_object) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Service Object",
					filters: { name: frm.doc.service_object },
					fieldname: ["project", "customer"],
				},
				callback: function (r) {
					if (r.message) {
						frm.set_value("project", r.message.project || "");
						frm.set_value("customer", r.message.customer || "");
					}
				},
			});
		} else {
			frm.set_value("project", "");
			frm.set_value("customer", "");
		}
	},
});
