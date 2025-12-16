import frappe

def verify_setup():
    print("\n--- Verification ---")

    # Check Price List
    price_list_exists = frappe.db.exists("Price List", "USD Selling")
    print(f"Price List 'USD Selling' exists: {price_list_exists}")

    # Check Currency Exchange Rates
    currency_exchanges = frappe.db.get_all("Currency Exchange", fields=["name", "from_currency", "to_currency", "exchange_rate"])
    print(f"Found {len(currency_exchanges)} Currency Exchange records.")
    for exchange in currency_exchanges:
        print(f"  - {exchange['from_currency']} to {exchange['to_currency']}: Rate={exchange['exchange_rate']}, Name={exchange['name']}")

    # Verify get_exchange_rate function (check for errors)
    print("\nVerifying `erpnext.setup.utils.get_exchange_rate` function...")
    try:
        # Test with known currencies
        rate_rub_usd = frappe.get_attr("erpnext.setup.utils.get_exchange_rate")('RUB', 'USD')
        rate_usd_rub = frappe.get_attr("erpnext.setup.utils.get_exchange_rate")('USD', 'RUB')
        print(f"  - RUB to USD exchange rate (via get_exchange_rate): {rate_rub_usd}")
        print(f"  - USD to RUB exchange rate (via get_exchange_rate): {rate_usd_rub}")
        print("\n`erpnext.setup.utils.get_exchange_rate` function executed without errors.")
    except Exception as e:
        print(f"Error calling `erpnext.setup.utils.get_exchange_rate`: {e}")

# Initialize Frappe context and execute verification
# This part is crucial for running verification outside of bench console/execute context directly.
# However, for safety and to ensure proper initialization, we'll use bench execute.

# The following lines are for direct script execution. 
# If running via bench execute, Frappe context is managed by bench.
# If bench execute fails, this means site context is still an issue.
# We'll rely on bench execute to handle initialization correctly.

# For now, we just define the function. The execution will be handled by bench.

