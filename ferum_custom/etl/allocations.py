import re
import frappe


def try_allocate_by_doc_ref(payment_name: str):
    pay = frappe.get_doc("Payment", payment_name)
    if getattr(pay, "direction", None) != "in":
        return
    text = (pay.doc_ref or "")
    # Extract invoice numbers from doc_ref in common formats (e.g., "счёт №123" or "№ 123")
    nums = re.findall(r'(?:сч[её]т[ау]?\s*№?\s*|№\s*)(\d+)', text, re.I)
    remaining = float(pay.amount or 0)
    for n in nums:
        inv = frappe.db.sql(
            """
                select name, amount
                from `tabInvoice`
                where company=%s and invoice_no=%s
            """,
            (pay.company, n),
            as_dict=True,
        )
        if not inv:
            continue
        inv = inv[0]
        due = frappe.db.sql(
            """
                select (i.amount - coalesce(sum(a.amount),0)) as due
                from `tabInvoice` i
                left join `tabPayment Allocation` a on a.invoice=i.name
                where i.name=%s
                group by i.amount
            """,
            (inv.name,),
            as_dict=True,
        )
        due_amt = float(due[0].due) if due else float(inv.amount)
        alloc = min(remaining, due_amt)
        if alloc > 0:
            frappe.get_doc(
                {
                    "doctype": "Payment Allocation",
                    "payment": pay.name,
                    "invoice": inv.name,
                    "amount": alloc,
                }
            ).insert(ignore_permissions=True)
            remaining -= alloc
        if remaining <= 0:
            break

