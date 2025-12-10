import time

import frappe
from frappe.rate_limiter import rate_limit

from ferum_custom.ferum_custom.metrics import iter_counters


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=60, methods=["GET"])  # 60 req/min per IP
def prometheus() -> None:
	"""Return a simple Prometheus metrics exposition.

	Exposes a few business and system metrics without external deps.
	"""

	open_requests = frappe.db.count("Issue", {"status": ["not in", ["Resolved", "Closed"]]})
	sent_invoices = frappe.db.count("Sales Invoice", {"status": "Sent"})
	paid_invoices = frappe.db.count("Sales Invoice", {"status": "Paid"})

	lines: list[str] = []
	ts = int(time.time())
	lines.append("# HELP ferum_open_service_requests Count of open service requests")
	lines.append("# TYPE ferum_open_service_requests gauge")
	lines.append(f"ferum_open_service_requests {open_requests} {ts}")

	lines.append("# HELP ferum_invoices_sent Count of invoices with status=Sent")
	lines.append("# TYPE ferum_invoices_sent gauge")
	lines.append(f"ferum_invoices_sent {sent_invoices} {ts}")

	lines.append("# HELP ferum_invoices_paid Count of invoices with status=Paid")
	lines.append("# TYPE ferum_invoices_paid gauge")
	lines.append(f"ferum_invoices_paid {paid_invoices} {ts}")

	# Export integration counters
	for name, labels, value in iter_counters():
		# metric naming: already namespaced at definition site
		if labels:
			lbl = ",".join(f'{k}="{v}"' for k, v in labels.items())
			lines.append(f"{name}{{{lbl}}} {value} {ts}")
		else:
			lines.append(f"{name} {value} {ts}")

	try:
		import psutil  # type: ignore[import-untyped]

		lines.append("# HELP process_cpu_percent CPU percent of the Python process")
		lines.append("# TYPE process_cpu_percent gauge")
		lines.append(f"process_cpu_percent {psutil.Process().cpu_percent(interval=None)} {ts}")

		mem = psutil.virtual_memory()
		lines.append("# HELP system_memory_used_bytes System memory used (bytes)")
		lines.append("# TYPE system_memory_used_bytes gauge")
		lines.append(f"system_memory_used_bytes {mem.used} {ts}")
	except Exception:
		pass

	frappe.local.response.update(
		{
			"type": "txt",
			"filename": None,
			"content_type": "text/plain; version=0.0.4; charset=utf-8",
			"message": "\n".join(lines) + "\n",
		}
	)
