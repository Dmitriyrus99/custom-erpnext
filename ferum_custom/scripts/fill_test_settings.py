import json

import frappe

SERVICE_ACCOUNT = {
	"type": "service_account",
	"project_id": "gen-lang-client-0978319267",
	"private_key_id": "792be9dc56a28864a5a0c4124d050947e1da148e",
	"private_key": """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQClVytCLAhujRsx
yMmtmJ0pCPKghmPMk1tvYLdO41geiMlfsRTxnHc7P0uqcbMsHn3SNfrJetSqzal8
3E9XZVlXSyiqQdNNmCiX7Je48PtNA8uLfjzGJCVnrfT+PGnf0+9ayls/z1OT5RUy
hacdF2xy1TvsrKWmAWf2x/PNaFsWxVgcoSBEwm3UlKcceQdlFcK9jcM31R1a1oGF
L8hwrobN9VQ5E+o3eOAyJR1stwigEN6iEvXv67ymhYAdnKv35Dn0drQVSnuKV9zm
dQvyRItIixjBMfcI3QX/NcQRU3+FHEWLOTSEv2xUx86k05UG7a48hT75E5J6L+Z+
8ccZHbz7AgMBAAECggEAAzFDd+tzyDnovH0uK1S/ZQvMNNaNWpxcWGMrgxxDjc7+
8eqCqLR6re2JQDeP2QNmLpSsYfzQqcby81/UL7Aeuy6Lrz86RR804H52n5gKDS9q
4iebAHdcJ+nUpPPyGWPHdszcEGwiCFkImdDqNXudIhbFNcr6XHyndqSuhzdMlvPE
zmrUDHEwCMSnnnl+4cKW4ytigfKhs4eNPt/PT38GE+SMBveJ0nWz77PncsMtLql6
BD3Eqy+afsOnjNk+RP9hwiG0wf4phie+3zwDoPWCeZ3u6FakObaNNObidknWkjI6
wibT/Phio8kAQP8r+yQ/JR8RvetMv0TuCiPAGFVnmQKBgQDUv2jX0lmEtFiRtfZJ
7XDMt49xKD0RduPlCXv3SUzQzV6hipKRmFU7eHLfwu8PS2KRiYw8UPr07r5Cp+d6
K8gi9u/zIP3wGQeL6PGhDMVwVRIK/8rOf+24IQSg/9xmVGrnkvbJDGEBxf/YsVlx
sg0udV1pCuLijoIs5Oa7VpJU6QKBgQDG9Gv5drE9d8fmgas7AnYo53jQsgwKC/QI
zL05tWkW/xRxama7hqU6P8uayXhLp3bmgF4eP7Wy5bv49r/DSMR8wysGb3Kh/RUE
BD8IJbNvJwvCftCYbitfLyioceZnuzUWbh/MC4i5acxDj26hWnxgWI+rukt89EjB
OOuqPGLkQwKBgG4R1fmLcBszf3trzE/1U93mvoUKD4Zgn4nZPVT0jJSfHG2xlyFS
0g4hxDU20p50HzwzEOYH878TYkZ0PlO8ISDN59k/YYJ+QKRHUfRD+kajDOG588Cg
+WnBU3bEyc/7rw++voXILMxRF4ySPTeQqjc2K6z0H+ydVIZLq4CTSsQ5AoGAEPOi
f47tax9ZmPpTbKO5DaMrWBzTicea82T+enxKh/sT8tXuCuxeB6iH4Jhp94g9SUaG
vm0PPj701TGxBSKeG0NF1zaHveWidMUn2bncoAvjpJ7JhzNb3rBV9oQ97Xi1/UNE
0k3pSGMLVHZUJste7ZaeJzOoWu01hcEj001x36ECgYAFFMYeRnEwo2wnUnI+NsH1
Yzkbz/wgXDs7oqcgnwN5QCLr4lA4UwMkkpZNyiV79b5ygEhE0annJOpjX1Bm/DoH
eEhBh+G1xq7Pw3Zrl0BNOBCbkc+qVIZIOYrfmqTr9eSl4qetVQLTkzOH8IWh86Ze
E94+LGmM8c4U4Pf2tB2seg==
-----END PRIVATE KEY-----""",
	"client_email": "erp-185@gen-lang-client-0978319267.iam.gserviceaccount.com",
	"client_id": "106007535860776173950",
	"auth_uri": "https://accounts.google.com/o/oauth2/auth",
	"token_uri": "https://oauth2.googleapis.com/token",
	"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
	"client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/erp-185%40gen-lang-client-0978319267.iam.gserviceaccount.com",
	"universe_domain": "googleapis.com",
}


def run():
	frappe.set_user("Administrator")
	payload = json.dumps(SERVICE_ACCOUNT, indent=2)

	existing = frappe.db.exists(
		"File",
		{
			"attached_to_doctype": "Ferum Custom Settings",
			"attached_to_name": "Ferum Custom Settings",
			"file_name": "ferum-service-account.json",
		},
	)
	if existing:
		frappe.delete_doc("File", existing, ignore_permissions=True)

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": "ferum-service-account.json",
			"content": payload,
			"is_private": 1,
		}
	).insert(ignore_permissions=True)

	frappe.db.set_single_value("Ferum Custom Settings", "google_service_account_json", file_doc.file_url)
	frappe.db.set_single_value("Ferum Custom Settings", "enable_google_drive_sync", 1)
	frappe.db.set_single_value("Ferum Custom Settings", "enable_google_sheets_sync", 1)
	frappe.db.set_single_value("Ferum Custom Settings", "google_drive_root_folder_id", "ferum-drive-root-test")
	frappe.db.set_single_value("Ferum Custom Settings", "enable_jwt", 1)
	frappe.db.set_single_value("Ferum Custom Settings", "jwt_secret", "test-jwt-secret")

	frappe.db.commit()
	return {"file_url": file_doc.file_url}
