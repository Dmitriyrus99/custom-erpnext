import json
import pandas as pd
import frappe


def ingest_excel_to_staging(path, company=None, sheet=None, source_name=None):
	df = pd.read_excel(path, sheet_name=sheet) if sheet else pd.read_excel(path)
	for _, row in df.iterrows():
		doc = frappe.get_doc(
			{
				"doctype": "stg_raw",
				"company": company,
				"source_file": source_name or path,
				"sheet": sheet,
				"row_json": json.dumps(row.to_dict(), ensure_ascii=False),
			}
		)
		doc.insert(ignore_permissions=True)
