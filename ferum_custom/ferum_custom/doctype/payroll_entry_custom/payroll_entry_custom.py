import frappe
from frappe.model.document import Document


class PayrollEntryCustom(Document):
	def validate(self):
		self.calculate_total_payroll_amount()

	def calculate_total_payroll_amount(self):
		self.total_payroll_amount = 0
		for item in self.employees:
			self.total_payroll_amount += item.net_salary
