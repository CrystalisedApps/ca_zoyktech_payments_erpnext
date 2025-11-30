import frappe
from frappe import _

def get_context(context):
    """Context for payment failed page - uses templates/pages/payment_failed.html"""
    context.no_cache = 1
    
    reference = frappe.form_dict.get('reference')
    if reference:
        try:
            payment_txn = frappe.get_doc("Payment Transaction", reference)
            context.payment_info = {
                'reference': payment_txn.reference_id,
                'amount': payment_txn.amount,
                'currency': payment_txn.currency,
                'failure_reason': payment_txn.failure_reason,
                'customer_email': payment_txn.customer_email
            }
            if payment_txn.payment_initiated:
                context.payment_info['payment_initiated'] = payment_txn.payment_initiated
            
            # Get retry URL
            payment_links = frappe.get_all("Payment Link",
                filters={"reference_id": reference},
                fields=["payment_url"]
            )
            
            if payment_links and payment_links[0].get('payment_url'):
                context.payment_info['retry_url'] = payment_links[0]['payment_url']
            else:
                context.payment_info['retry_url'] = f"/payment?reference={reference}"
                
        except frappe.DoesNotExistError:
            context.payment_info = None
            context.error = _("Payment reference not found")
    else:
        context.payment_info = None
        context.error = _("No payment reference provided")
    
    return context