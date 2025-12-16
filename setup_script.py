import frappe
import sys
import os

# Define bench path and add it to sys.path
bench_path = "/home/frappe/frappe-bench"
sys.path.insert(0, bench_path)

# Add the specific app directory to sys.path
app_dir = os.path.join(bench_path, "apps", "ferum_custom")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Initialize Frappe context
frappe.init(site="erpclone.ferumrus.ru")
frappe.connect()

try:
    # Import the setup function from the stage1_setup script
    # This relies on the app directory being in sys.path
    import ferum_custom.scripts.stage1_setup
    ferum_custom.scripts.stage1_setup.setup_financials()
    
    print("\n--- Setup Summary ---")
    print("Financial and currency setup script executed successfully.")
    print("Please note that exchange rates are set to placeholder values.")
    print("Further verification of `erpnext.setup.utils.get_exchange_rate` will be performed.")

except Exception as e:
    print(f"An error occurred during script execution: {e}")
    frappe.db.rollback()
finally:
    frappe.destroy()
