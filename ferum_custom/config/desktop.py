from __future__ import annotations

from frappe import _


def get_data():
    module_names = [
        "Project & Contract Management",
        "Issue Management",
        "Work Reporting",
        "Invoicing",
        "HR & Payroll",
        "Document Management",
        "Notifications",
        "Analytics",
        "Ferum Custom",
    ]

    colors = [
        "#5A8DEE",
        "#39DA8A",
        "#FF9F43",
        "#FF6B6B",
        "#1E9FF2",
        "#9C27B0",
        "#FF7043",
        "#2A3F54",
        "#1A237E",
    ]

    icons = [
        "octicon octicon-briefcase",
        "octicon octicon-tasklist",
        "octicon octicon-ruby",
        "octicon octicon-credit-card",
        "octicon octicon-people",
        "octicon octicon-file-directory",
        "octicon octicon-bell",
        "octicon octicon-graph",
        "octicon octicon-apps",
    ]

    data = []
    for name, color, icon in zip(module_names, colors, icons):
        data.append(
            {
                "module_name": name,
                "color": color,
                "icon": icon,
                "label": _(name),
                "type": "module",
            }
        )
    return data
