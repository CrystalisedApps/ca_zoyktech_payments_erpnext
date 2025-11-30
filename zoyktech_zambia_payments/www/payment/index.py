import frappe
from frappe import _

def get_context(context):
    """Context for payment page - uses templates/pages/payment.html"""
    context.no_cache = 1
    
    # Get payment reference from query string
    reference = frappe.form_dict.get('reference')
    if reference:
        try:
            payment_link = frappe.get_doc("Payment Link", reference)
            context.payment_info = {
                'reference': payment_link.reference_id,
                'amount': payment_link.amount,
                'currency': payment_link.currency,
                'description': payment_link.description,
                'customer_email': payment_link.customer_email,
                'customer_phone': payment_link.customer_phone
            }
            
            # Check if expired
            if hasattr(payment_link, 'is_expired') and payment_link.is_expired():
                context.payment_info['expired'] = True
            else:
                context.payment_info['expired'] = False
                
        except frappe.DoesNotExistError:
            try:
                payment_txn = frappe.get_doc("Payment Transaction", reference)
                context.payment_info = {
                    'reference': payment_txn.reference_id,
                    'amount': payment_txn.amount,
                    'currency': payment_txn.currency,
                    'customer_email': payment_txn.customer_email,
                    'customer_phone': payment_txn.customer_phone,
                    'expired': False
                }
            except frappe.DoesNotExistError:
                context.payment_info = None
                context.error = _("Payment reference not found")
    else:
        context.payment_info = None
        context.error = _("No payment reference provided")
    
    return context