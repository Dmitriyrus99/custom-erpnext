import frappe
from frappe.model.document import Document


class PayrollEntryCustom(Document):
	def validate(self):
		self.calculate_totals_and_validate_items()
		self.apply_service_report_earnings()

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

	def apply_service_report_earnings(self):
		"""Augment/initialize base salaries from Timesheet Detail within period.

		For each employee row, sum hours from Timesheets with status in
		(Submitted, Approved) and start_date/end_date within [period_start, period_end].
		If base_salary is zero, set it from this sum. Recompute net_salary.
		"""
		try:
			start = getattr(self, "period_start", None)
			end = getattr(self, "period_end", None)
			if not start or not end:
				return
			rows = {row.employee: row for row in self.employees if getattr(row, "employee", None)}
			if not rows:
				return
			employees = list(rows.keys())
			# Sum totals from time logs joined via parent Timesheet
			data = frappe.db.sql(
				"""
                select w.employee, sum(w.hours) as amount
                from `tabTimesheet Detail` w
                join `tabTimesheet` r on r.name = w.parent
                where w.employee in %(emps)s
                  and r.start_date >= %(start)s and r.end_date <= %(end)s
                  and r.status in ('Submitted','Approved')
                group by w.employee
                """,
				{"emps": tuple(employees), "start": start, "end": end},
			)
			amounts = {emp: amt or 0 for emp, amt in data}
			# Update rows
			self.total_payroll_amount = 0
			for emp, row in rows.items():
				from_reports = amounts.get(emp, 0) or 0
				if (row.base_salary or 0) == 0 and from_reports:
					row.base_salary = from_reports
				# recompute net
				row.net_salary = (row.base_salary or 0) - (row.advance or 0)
				self.total_payroll_amount += row.net_salary
		except Exception:
			# Don't block payroll on aggregation errors
			pass
