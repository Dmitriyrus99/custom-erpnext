import frappe


def setup_financials():
    company_name = "Ferum Co" # Assumed based on prompt

    # --- Price List Setup ---
    usd_price_list_name = "USD Standard Price List"

    price_lists = frappe.get_list("Price List", filters={"currency": "USD"}, fields=["name"])

    if not price_lists:
        try:
            company_doc = frappe.get_doc("Company", company_name)
            if not company_doc:
                print(f"Company '{company_name}' not found. Cannot create USD Price List.")
                frappe.db.rollback()
                return

            new_price_list = frappe.new_doc("Price List")
            new_price_list.name = usd_price_list_name
            new_price_list.currency = "USD"
            new_price_list.price_list_name = usd_price_list_name
            new_price_list.company = company_doc.name
            new_price_list.insert()
            frappe.db.commit()
            print(f"Created USD Price List: {usd_price_list_name}")
        except Exception as e:
            print(f"Error creating USD Price List: {e}")
            frappe.db.rollback()
    else:
        print(f"USD Price List already exists: {price_lists[0].name}")

    # --- Currency Exchange Rate Setup ---
    rub_usd_exchange_rate_placeholder = 0.01
    usd_rub_exchange_rate_placeholder = 100.0

    # RUB to USD
    rub_to_usd_exchanges = frappe.get_list("Currency Exchange", filters={"from_currency": "RUB", "to_currency": "USD"}, fields=["name"])
    if not rub_to_usd_exchanges:
        try:
            new_exchange_rate = frappe.new_doc("Currency Exchange")
            new_exchange_rate.from_currency = "RUB"
            new_exchange_rate.to_currency = "USD"
            new_exchange_rate.exchange_rate = rub_usd_exchange_rate_placeholder
            new_exchange_rate.enable_manual_rate = 1
            new_exchange_rate.insert()
            frappe.db.commit()
            print(f"Seeded RUB to USD exchange rate: {rub_usd_exchange_rate_placeholder}")
        except Exception as e:
            print(f"Error seeding RUB to USD exchange rate: {e}")
            frappe.db.rollback()
    else:
        print(f"RUB to USD exchange rate already exists: {rub_to_usd_exchanges[0].name}")

    # USD to RUB
    usd_to_rub_exchanges = frappe.get_list("Currency Exchange", filters={"from_currency": "USD", "to_currency": "RUB"}, fields=["name"])
    if not usd_to_rub_exchanges:
        try:
            new_exchange_rate = frappe.new_doc("Currency Exchange")
            new_exchange_rate.from_currency = "USD"
            new_exchange_rate.to_currency = "RUB"
            new_exchange_rate.exchange_rate = usd_rub_exchange_rate_placeholder
            new_exchange_rate.enable_manual_rate = 1
            new_exchange_rate.insert()
            frappe.db.commit()
            print(f"Seeded USD to RUB exchange rate: {usd_rub_exchange_rate_placeholder}")
        except Exception as e:
            print(f"Error seeding USD to RUB exchange rate: {e}")
            frappe.db.rollback()
    else:
        print(f"USD to RUB exchange rate already exists: {usd_to_rub_exchanges[0].name}")

    print("\n--- Setup Summary ---")
    print("Financial and currency setup script executed.")
    print("Please note that exchange rates are set to placeholder values.")
    print("Further verification of `erpnext.setup.utils.get_exchange_rate` will be performed.")

# The function call `setup_financials()` is now part of the module imported by bench execute.
# No need for if __name__ == "__main__" block if executed via bench execute.
