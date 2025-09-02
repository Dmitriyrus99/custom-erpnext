frappe.ui.form.on("Service Request", {
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
