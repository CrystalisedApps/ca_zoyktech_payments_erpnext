import frappe
from frappe import _

def get_context(context):
    """Context for payment success page - uses templates/pages/payment_success.html"""
    context.no_cache = 1
    
    reference = frappe.form_dict.get('reference')
    if reference:
        try:
            payment_txn = frappe.get_doc("Payment Transaction", reference)
            context.payment_info = {
                'reference': payment_txn.reference_id,
                'amount': payment_txn.amount,
                'currency': payment_txn.currency,
                'transaction_id': payment_txn.transaction_id,
                'payment_method': payment_txn.payment_method,
                'customer_email': payment_txn.customer_email
            }
            if payment_txn.payment_completed:
                context.payment_info['payment_completed'] = payment_txn.payment_completed
                
        except frappe.DoesNotExistError:
            context.payment_info = None
            context.error = _("Payment reference not found")
    else:
        context.payment_info = None
        context.error = _("No payment reference provided")
    
    return context