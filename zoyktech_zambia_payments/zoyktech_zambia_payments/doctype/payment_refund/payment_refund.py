import frappe
from frappe.model.document import Document
from frappe import _
from datetime import datetime

class PaymentRefund(Document):
    def validate(self):
        self.validate_refund_amount()
        self.validate_payment_reference()
    
    def before_insert(self):
        self.set_default_values()
    
    def on_submit(self):
        self.process_refund()
    
    def validate_refund_amount(self):
        """Validate refund amount doesn't exceed original amount"""
        if self.refund_amount <= 0:
            frappe.throw(_("Refund amount must be greater than 0"))
        
        if self.refund_amount > self.original_amount:
            frappe.throw(_("Refund amount cannot exceed original amount"))
    
    def validate_payment_reference(self):
        """Validate payment reference exists and is completed"""
        try:
            payment_txn = frappe.get_doc("Payment Transaction", self.payment_reference)
            if payment_txn.status != "Completed":
                frappe.throw(_("Can only refund completed payments"))
        except frappe.DoesNotExistError:
            frappe.throw(_("Payment reference not found"))
    
    def set_default_values(self):
        """Set default values for new refund"""
        if not self.refund_initiated_by:
            self.refund_initiated_by = frappe.session.user
        
        if not self.refund_initiated_date:
            self.refund_initiated_date = datetime.now()
        
        # Get original payment details
        try:
            payment_txn = frappe.get_doc("Payment Transaction", self.payment_reference)
            self.original_amount = payment_txn.amount
            self.currency = payment_txn.currency
            self.customer_email = payment_txn.customer_email
            self.customer_phone = payment_txn.customer_phone
        except frappe.DoesNotExistError:
            pass
    
    def process_refund(self):
        """Process refund with payment gateway"""
        try:
            from zoyktech_zambia_payments.api.zoyktech_client import ZoykTechClient
            
            # Get payment transaction
            payment_txn = frappe.get_doc("Payment Transaction", self.payment_reference)
            
            # Prepare refund data
            refund_data = {
                "transaction_id": payment_txn.transaction_id,
                "amount": self.refund_amount,
                "reason": self.reason,
                "reference": self.name
            }
            
            # Process refund with gateway
            client = ZoykTechClient()
            refund_response = client.refund_payment(refund_data)
            
            # Update refund record
            self.transaction_id = refund_response.get("refund_transaction_id")
            self.gateway_response = str(refund_response)
            self.status = "Completed"
            self.refund_completed_date = datetime.now()
            
            # Update payment transaction status
            payment_txn.status = "Refunded"
            payment_txn.save()
            
            # Create system note
            frappe.msgprint(_("Refund processed successfully"))
            
        except Exception as e:
            frappe.log_error(f"Error processing refund: {str(e)}", "Refund Processing")
            self.status = "Failed"
            frappe.throw(_("Failed to process refund: {0}").format(str(e)))
    
    def on_cancel(self):
        """Handle refund cancellation"""
        if self.status == "Completed":
            frappe.throw(_("Cannot cancel a completed refund"))

@frappe.whitelist()
def create_refund(payment_reference, refund_amount, reason="Customer request"):
    """Create a new refund request"""
    try:
        # Check if refund already exists for this payment
        existing_refunds = frappe.get_all("Payment Refund",
            filters={"payment_reference": payment_reference, "docstatus": ["<", 2]},
            fields=["name"]
        )
        
        if existing_refunds:
            return {
                "success": False,
                "message": _("Refund already exists for this payment")
            }
        
        # Create refund
        refund = frappe.new_doc("Payment Refund")
        refund.payment_reference = payment_reference
        refund.refund_amount = float(refund_amount)
        refund.reason = reason
        refund.insert()
        
        return {
            "success": True,
            "refund": refund.name,
            "message": _("Refund created successfully")
        }
    
    except Exception as e:
        frappe.log_error(f"Error creating refund: {str(e)}", "Refund Creation")
        return {
            "success": False,
            "error": str(e),
            "message": _("Failed to create refund")
        }

@frappe.whitelist()
def get_refund_status(refund_name):
    """Get refund status"""
    try:
        refund = frappe.get_doc("Payment Refund", refund_name)
        
        return {
            "success": True,
            "status": refund.status,
            "refund_amount": refund.refund_amount,
            "currency": refund.currency,
            "transaction_id": refund.transaction_id
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }