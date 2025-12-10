frappe.query_reports["Upcoming Maintenance Tasks"] = {
  filters: [
    {
      fieldname: "preset_range",
      label: __("Preset Range"),
      fieldtype: "Select",
      options: ["Next 7 Days", "Next 30 Days"].join("\n"),
      default: "Next 7 Days",
    },
    { fieldname: "from_date", label: __("From"), fieldtype: "Date" },
    { fieldname: "to_date", label: __("To"), fieldtype: "Date" },
    {
      fieldname: "project",
      label: __("Project"),
      fieldtype: "Link",
      options: "Service Project",
    },
    { fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" },
  ],

  onload(report) {
    ["project", "customer"].forEach((k) => {
      if (report.get_filter_value(k) === undefined) report.set_filter_value(k, null);
    });
  },
};

