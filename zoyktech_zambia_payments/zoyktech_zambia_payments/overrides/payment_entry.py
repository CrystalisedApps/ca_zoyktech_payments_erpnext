# payment_entry.py

import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry as OriginalPaymentEntry

class CustomPaymentEntry(OriginalPaymentEntry):
    """Custom Payment Entry class with subscription support"""
    pass

@frappe.whitelist()
def make_payment_entry(*args, **kwargs):
    """Wrapper for make_payment_entry"""
    from erpnext.accounts.doctype.payment_entry.payment_entry import make_payment_entry as original_make_payment_entry
    return original_make_payment_entry(*args, **kwargs)

@frappe.whitelist()
def get_payment_entry(*args, **kwargs):
    """Wrapper for get_payment_entry"""
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry as original_get_payment_entry
    return original_get_payment_entry(*args, **kwargs)