import frappe
from frappe import _
from ..api.payment_integration import PaymentIntegration

def create_payment_link_on_submit(doc, method=None):
    """
    Automatically create payment link when Sales Invoice is submitted
    This is called via doc_events hook
    """
    try:
        # Only create payment link if there's outstanding amount
        if doc.docstatus == 1 and doc.outstanding_amount > 0:
            # Check if auto-create is enabled in settings
            settings = frappe.get_single("Payment Gateway Settings")
            if getattr(settings, 'auto_create_payment_links', False):
                integration = PaymentIntegration()
                
                # Prepare payment data
                payment_data = {
                    'doctype': 'Sales Invoice',
                    'docname': doc.name,
                    'customer_email': doc.contact_email or doc.customer_email,
                    'customer_phone': doc.contact_phone or doc.customer_phone
                }
                
                # Create payment request
                result = integration.create_payment_request(**payment_data)
                
                if result.get('success'):
                    frappe.msgprint(_("Payment link created automatically"))
                    frappe.logger().info(f"Auto-created payment link for Sales Invoice {doc.name}")
                else:
                    frappe.log_error(f"Failed to auto-create payment link: {result.get('message')}", "Payment Auto-Create")
    
    except Exception as e:
        frappe.log_error(f"Error in create_payment_link_on_submit: {str(e)}", "Invoice Handler")

def handle_payment_authorization(doc, method=None):
    """
    Handle payment authorization for Sales Invoice
    """
    try:
        # This would be called when a payment is authorized
        # You can add custom logic here for payment authorization
        pass
        
    except Exception as e:
        frappe.log_error(f"Error in handle_payment_authorization: {str(e)}", "Payment Authorization")