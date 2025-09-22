import frappe
from frappe.model.document import Document


class PayrollEntryCustom(Document):
	def validate(self):
		self.calculate_totals_and_validate_items()

	def calculate_totals_and_validate_items(self):
		self.total_payroll_amount = 0
		for item in self.employees:
			# derive net salary from base - advance
			base = item.base_salary or 0
			adv = item.advance or 0
			if adv > base:
				raise frappe.ValidationError(
					frappe._("Advance cannot exceed Base Salary for employee {0}").format(
						getattr(item, "employee", "")
					)
				)
			item.net_salary = base - adv
			self.total_payroll_amount += item.net_salary
