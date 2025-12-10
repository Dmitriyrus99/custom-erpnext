from __future__ import annotations

import frappe
from frappe.tests.utils import FrappeTestCase

from ferum_custom.ferum_custom.api import service
from ferum_custom.ferum_custom.tests import smoke_tools


class TestServiceAPI(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.company = smoke_tools.ensure_company()
		cls.customer = smoke_tools.ensure_customer("Test Customer", company=cls.company)
		cls.asset = smoke_tools.ensure_asset("Test Asset 1", customer=cls.customer, company=cls.company)
		cls.project = smoke_tools.ensure_project_doc("Test Project 1", customer=cls.customer)

		# Ensure 'Client' role exists and assign it to a test user
		if not frappe.db.exists("Role", "Client"):
			frappe.get_doc({"doctype": "Role", "role_name": "Client"}).insert(ignore_permissions=True)

		if not frappe.db.exists("User", "test_client@example.com"):
			client_user = frappe.get_doc(
				{
					"doctype": "User",
					"email": "test_client@example.com",
					"first_name": "Test",
					"last_name": "Client",
					"user_type": "Website User",
					"enabled": 1,
				}
			)
			client_user.insert(ignore_permissions=True)
			client_user.add_roles("Client")

		# Grant User Permission for the client to their customer
		if not frappe.db.exists(
			"User Permission",
			{"user": "test_client@example.com", "allow": "Customer", "for_value": cls.customer},
		):
			up = frappe.new_doc("User Permission")
			up.user = "test_client@example.com"
			up.allow = "Customer"
			up.for_value = cls.customer
			up.insert(ignore_permissions=True)

		# Ensure Client has Read permission on Issue
		if not frappe.db.exists("Custom DocPerm", {"parent": "Issue", "role": "Client", "read": 1}):
			# We can't easily add Custom DocPerm via test if not already there,
			# but we can check if there's any permission.
			# Assuming standard ERPNext setup might lack Client -> Issue read if we don't enable it.
			# We will force add it to standard Issue permissions via property setter or custom docperm
			# For test stability, let's add a Custom DocPerm
			d = frappe.new_doc("Custom DocPerm")
			d.parent = "Issue"
			d.role = "Client"
			d.read = 1
			d.write = 0
			d.create = 1
			d.insert(ignore_permissions=True)

		frappe.clear_cache(user="test_client@example.com")

	def test_create_issue_api(self):
		frappe.set_user("Administrator")

		# Test with minimal fields
		result = service.create_issue(title="API Test Issue 1", description="Description 1")
		self.assertEqual(result["status"], "ok")
		self.assertTrue(result["name"].startswith("ISS-"))
		self.assertTrue(frappe.db.exists("Issue", result["name"]))

		issue_doc = frappe.get_doc("Issue", result["name"])
		self.assertEqual(issue_doc.subject, "API Test Issue 1")
		self.assertEqual(issue_doc.description, "Description 1")
		self.assertEqual(issue_doc.status, "Open")

		# Test with asset field (others inferred)
		result2 = service.create_issue(
			title="API Test Issue 2", description="Description 2", asset=self.asset
		)
		self.assertEqual(result2["status"], "ok")
		issue_doc2 = frappe.get_doc("Issue", result2["name"])
		self.assertEqual(issue_doc2.subject, "API Test Issue 2")
		# Custom field is 'service_object' pointing to Asset
		self.assertEqual(issue_doc2.service_object, self.asset)
		# Check inferred fields
		self.assertEqual(issue_doc2.company, self.company)
		self.assertEqual(issue_doc2.customer, self.customer)
		self.assertEqual(issue_doc2.status, "Open")

	def test_list_issues_api_admin(self):
		frappe.set_user("Administrator")
		# Create a few issues for testing
		service.create_issue(title="List Test Issue 1")
		service.create_issue(title="List Test Issue 2")

		result = service.list_issues()
		self.assertEqual(result["status"], "ok")
		self.assertTrue(len(result["data"]) >= 2)  # Should see at least the created ones

		# Test filtering by status
		result_open = service.list_issues(status="Open")
		self.assertEqual(result_open["status"], "ok")
		for issue in result_open["data"]:
			self.assertEqual(issue["status"], "Open")

	def test_list_issues_api_client(self):
		frappe.set_user("test_client@example.com")

		# Create an issue for the client's customer (should be visible)
		# Use frappe.get_doc to bypass API limitations for test setup
		frappe.set_user("Administrator")
		# Ensure we don't hit LinkValidationError on service_object if it's still pointing to Service Object
		# We will skip asset for this test or ensure field is fixed.
		issue1 = frappe.get_doc(
			{
				"doctype": "Issue",
				"subject": "Client Issue 1",
				"customer": self.customer,
				"company": self.company,
				"status": "Open",
			}
		).insert(ignore_permissions=True)

		# Create an issue for a different customer (should not be visible)
		other_customer = smoke_tools.ensure_customer("Other Customer", company=self.company)
		issue2 = frappe.get_doc(
			{
				"doctype": "Issue",
				"subject": "Other Client Issue",
				"customer": other_customer,
				"company": self.company,
				"status": "Open",
			}
		).insert(ignore_permissions=True)

		frappe.set_user("test_client@example.com")
		result = service.list_issues()
		self.assertEqual(result["status"], "ok")

		# Verify that only issues for 'Test Customer' are visible
		# Check by name since list_issues returns dicts
		visible_names = [x["name"] for x in result["data"]]
		self.assertIn(issue1.name, visible_names)
		self.assertNotIn(issue2.name, visible_names)

		# Attempt to fetch a specific issue not belonging to the client's customer (should fail)
		# API throws validation error if customer check fails
		with self.assertRaises(frappe.PermissionError):
			service.get_issue(name=issue2.name)

		frappe.set_user("Administrator")  # Reset user

	def test_get_issue_api(self):
		frappe.set_user("Administrator")

		# Create an issue
		create_result = service.create_issue(title="Get Test Issue", description="Get Description")
		issue_name = create_result["name"]

		# Fetch the issue
		get_result = service.get_issue(name=issue_name)
		self.assertEqual(get_result["status"], "ok")
		self.assertEqual(get_result["data"]["name"], issue_name)
		self.assertEqual(get_result["data"]["title"], "Get Test Issue")  # API returns 'title'
		self.assertEqual(get_result["data"]["description"], "Get Description")

	def test_update_issue_status_api(self):
		frappe.set_user("Administrator")

		# Create an issue
		create_result = service.create_issue(title="Update Test Issue")
		issue_name = create_result["name"]

		# Update status
		update_result = service.update_issue_status(name=issue_name, status="Resolved")
		self.assertEqual(update_result["status"], "Resolved")
		self.assertEqual(update_result["name"], issue_name)

		# Verify status in DB
		updated_status = frappe.db.get_value("Issue", issue_name, "status")
		self.assertEqual(updated_status, "Resolved")

		# Test invalid status (should fall back to Open or be rejected by workflow)
		# Assuming fallback to Open as per original code logic or validation failure if strict
		# Since logic says 'if status in allowed else Open', it should revert to Open
		update_result_invalid = service.update_issue_status(name=issue_name, status="InvalidStatus")
		self.assertEqual(update_result_invalid["status"], "Open")
		self.assertEqual(frappe.db.get_value("Issue", issue_name, "status"), "Open")

	def test_confirm_issue_completion_api(self):
		frappe.set_user("Administrator")
		# Create an issue and set status to Resolved
		# API doesn't support status param, so update after creation or insert directly
		issue = frappe.get_doc(
			{
				"doctype": "Issue",
				"subject": "Confirm Test Issue",
				"status": "Resolved",
				"company": self.company,
			}
		).insert(ignore_permissions=True)
		issue_name = issue.name

		# Simulate client confirming completion
		frappe.set_user("test_client@example.com")
		service.confirm_issue_completion(name=issue_name)

		# Verify a comment was added
		comments = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "Issue", "reference_name": issue_name, "comment_type": "Comment"},
		)
		self.assertTrue(len(comments) > 0)
		self.assertTrue(
			"Client confirmed completion" in frappe.get_doc("Comment", comments[0]["name"]).content
		)
		frappe.set_user("Administrator")

	def test_confirm_timesheet_report_api(self):
		frappe.set_user("Administrator")
		# Create an issue
		issue_name = smoke_tools.create_test_issue()
		# Create a timesheet linked to the issue
		timesheet_name = smoke_tools._get_or_create_timesheet(issue_name, "demo_attachment")

		# Simulate client confirming timesheet report
		frappe.set_user("test_client@example.com")
		service.confirm_timesheet_report(name=timesheet_name)

		# Verify a comment was added
		comments = frappe.get_all(
			"Comment",
			filters={
				"reference_doctype": "Timesheet",
				"reference_name": timesheet_name,
				"comment_type": "Comment",
			},
		)
		self.assertTrue(len(comments) > 0)
		self.assertTrue(
			"Client confirmed Timesheet Report" in frappe.get_doc("Comment", comments[0]["name"]).content
		)
		frappe.set_user("Administrator")
