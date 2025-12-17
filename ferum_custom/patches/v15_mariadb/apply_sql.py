import frappe

from . import execute_sql_block, iter_sql_files


def execute():
    for filename, sql in iter_sql_files():
        execute_sql_block(sql)
        frappe.logger().info("Executed SQL patch: %s", filename)
