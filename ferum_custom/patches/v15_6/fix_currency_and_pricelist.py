import frappe


def execute():
    frappe.reload_doc("accounts", "doctype", "currency_exchange")
    frappe.reload_doc("selling", "doctype", "price_list")

    ensure_usd_price_list()
    ensure_exchange_rate("RUB", "USD")
    ensure_exchange_rate("USD", "RUB")


def ensure_usd_price_list():
    if frappe.db.exists("Price List", "USD Selling"):
        return

    pl = frappe.get_doc(
        {
            "doctype": "Price List",
            "price_list_name": "USD Selling",
            "currency": "USD",
            "selling": 1,
            "enabled": 1,
        }
    )
    pl.insert(ignore_permissions=True)


def ensure_exchange_rate(from_currency, to_currency):
    if frappe.db.exists(
        "Currency Exchange", {"from_currency": from_currency, "to_currency": to_currency}
    ):
        return

    doc = frappe.get_doc(
        {
            "doctype": "Currency Exchange",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "exchange_rate": 1 if from_currency == to_currency else 90,
        }
    )
    doc.insert(ignore_permissions=True)
