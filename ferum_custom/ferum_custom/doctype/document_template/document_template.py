from __future__ import annotations

import frappe
from frappe.model.document import Document


class DocumentTemplate(Document):
    def validate(self):
        # Basic sanity: if output is PDF, suggest file extension in pattern
        try:
            if self.output == "PDF" and self.file_name_pattern and not self.file_name_pattern.lower().endswith(".pdf"):
                # Do not block, only warn in logs to keep UX simple
                frappe.logger().info("DocumentTemplate: file_name_pattern does not end with .pdf")
        except Exception:
            pass

