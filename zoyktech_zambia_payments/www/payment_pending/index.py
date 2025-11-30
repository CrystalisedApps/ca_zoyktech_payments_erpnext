import frappe
from frappe import _

def get_context(context):
    """Context for payment pending page - uses templates/pages/payment_pending.html"""
    context.no_cache = 1
    
    reference = frappe.form_dict.get('reference')
    if reference:
        try:
            payment_txn = frappe.get_doc("Payment Transaction", reference)
            context.payment_info = {
                'reference': payment_txn.reference_id,
                'amount': payment_txn.amount,
                'currency': payment_txn.currency,
                'customer_email': payment_txn.customer_email,
                'payment_method': payment_txn.payment_method
            }
            if payment_txn.payment_initiated:
                context.payment_info['payment_initiated'] = payment_txn.payment_initiated
                
        except frappe.DoesNotExistError:
            context.payment_info = None
            context.error = _("Payment reference not found")
    else:
        context.payment_info = None
        context.error = _("No payment reference provided")
    
    return context