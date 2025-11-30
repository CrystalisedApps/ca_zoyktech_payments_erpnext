import frappe
from frappe import _

def update_payment_gateway_status(doc, method=None):
    """
    Update payment gateway status when Payment Entry is submitted
    """
    try:
        # Check if this payment entry has a gateway reference
        if doc.custom_gateway_reference:
            # Update the payment transaction status
            try:
                payment_txn = frappe.get_doc("Payment Transaction", doc.custom_gateway_reference)
                if payment_txn:
                    payment_txn.status = "Completed"
                    payment_txn.save(ignore_permissions=True)
                    frappe.db.commit()
            except frappe.DoesNotExistError:
                pass
    
    except Exception as e:
        frappe.log_error(f"Error in update_payment_gateway_status: {str(e)}", "Payment Handler")

def handle_payment_cancellation(doc, method=None):
    """
    Handle payment cancellation
    """
    try:
        if doc.custom_gateway_reference:
            # Update payment transaction status to cancelled
            try:
                payment_txn = frappe.get_doc("Payment Transaction", doc.custom_gateway_reference)
                if payment_txn:
                    payment_txn.status = "Cancelled"
                    payment_txn.save(ignore_permissions=True)
                    frappe.db.commit()
            except frappe.DoesNotExistError:
                pass
    
    except Exception as e:
        frappe.log_error(f"Error in handle_payment_cancellation: {str(e)}", "Payment Handler")