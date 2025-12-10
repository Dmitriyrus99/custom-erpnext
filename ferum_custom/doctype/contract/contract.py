import re
import frappe
from frappe.model.document import Document


def _normalize(s: str) -> str:
	s = s or ""
	s = s.strip()
	s = re.sub(r"[ \u00A0]+", "", s)  # collapse spaces
	s = s.replace("—", "-").replace("–", "-")  # unify dashes
	s = s.replace("\\", "/")  # unify slashes
	return s.lower()


class Contract(Document):
	def validate(self):
		self.contract_no_normalized = _normalize(self.contract_no)
		if self.date_start and self.date_end and self.date_start > self.date_end:
			frappe.throw("date_start must be <= date_end")
