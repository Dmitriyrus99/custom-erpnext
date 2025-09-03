frappe.ui.form.on("Invoice", {
    onload(frm) {
        if (!frm.is_new()) return;
        if (frm.doc.counterparty_type) return;

        try {
            const params = frappe.utils.get_query_params ? frappe.utils.get_query_params() : {};
            let t = params.counterparty_type || (frappe.route_options && frappe.route_options.counterparty_type);
            if (typeof t === "string") {
                t = t.trim();
            }
            if (t === "Customer" || t === "Subcontractor") {
                frm.set_value("counterparty_type", t);
            }
        } catch (e) {
            // no-op
        }
    },
});

