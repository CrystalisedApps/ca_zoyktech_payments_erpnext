from frappe import whitelist
import frappe
from .payment_integration import PaymentIntegration
from .zoyktech_client import ZoykTechClient

@whitelist(allow_guest=True)
def get_payment_methods():
    """Get available payment methods"""
    client = ZoykTechClient()
    return client.get_payment_methods()

@whitelist()
def create_payment(doctype, docname, payment_method=None):
    """Create payment request for document"""
    integration = PaymentIntegration()
    return integration.create_payment_request(doctype, docname, payment_method)

@whitelist()
def get_payment_status(reference_id):
    """Get payment status"""
    integration = PaymentIntegration()
    return integration.get_payment_status(reference_id)

@whitelist()
def cancel_payment(reference_id):
    """Cancel payment request"""
    integration = PaymentIntegration()
    return integration.cancel_payment_request(reference_id)

@whitelist()
def process_refund(transaction_id, amount, reason=""):
    """Process refund for transaction"""
    client = ZoykTechClient()
    refund_data = {
        "transaction_id": transaction_id,
        "amount": amount,
        "reason": reason
    }
    return client.refund_payment(refund_data)

@whitelist(allow_guest=True)
def payment_success_page(reference_id):
    """Payment success page for customers"""
    try:
        payment_txn = frappe.get_doc("Payment Transaction", reference_id)
        return {
            "success": True,
            "payment": payment_txn,
            "message": "Payment completed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@whitelist(allow_guest=True)
def payment_failure_page(reference_id):
    """Payment failure page for customers"""
    try:
        payment_txn = frappe.get_doc("Payment Transaction", reference_id)
        return {
            "success": False,
            "payment": payment_txn,
            "message": "Payment failed"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }