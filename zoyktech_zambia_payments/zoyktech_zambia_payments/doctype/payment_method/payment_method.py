# payment_method.py
import frappe
from frappe.model.document import Document
from frappe import _

class PaymentMethod(Document):
    def validate(self):
        self.validate_processing_fees()
        self.validate_amount_limits()
    
    def validate_processing_fees(self):
        """Validate processing fee percentages"""
        if self.processing_fee_percentage < 0:
            frappe.throw(_("Processing fee percentage cannot be negative"))
        
        if self.processing_fee_percentage > 10:
            frappe.throw(_("Processing fee percentage cannot exceed 10%"))
    
    def validate_amount_limits(self):
        """Validate amount limits"""
        if self.minimum_amount < 0:
            frappe.throw(_("Minimum amount cannot be negative"))
        
        if self.maximum_amount <= 0:
            frappe.throw(_("Maximum amount must be greater than 0"))
        
        if self.minimum_amount > self.maximum_amount:
            frappe.throw(_("Minimum amount cannot be greater than maximum amount"))
    
    def calculate_processing_fee(self, amount):
        """Calculate processing fee for given amount"""
        percentage_fee = (amount * self.processing_fee_percentage) / 100
        total_fee = percentage_fee + (self.fixed_fee or 0)
        return min(total_fee, amount)  # Ensure fee doesn't exceed amount
    
    def is_amount_valid(self, amount):
        """Check if amount is within valid range for this payment method"""
        return self.minimum_amount <= amount <= self.maximum_amount

@frappe.whitelist()
def get_available_payment_methods(amount=None, currency="ZMW"):
    """Get available payment methods for given amount and currency"""
    try:
        filters = {
            "enabled": 1
        }
        
        # If test mode, include test mode enabled methods
        settings = frappe.get_single("Payment Gateway Settings")
        if settings.is_test_mode:
            filters["test_mode_enabled"] = 1
        
        payment_methods = frappe.get_all("Payment Method",
            filters=filters,
            fields=["payment_method", "processing_fee_percentage", "fixed_fee", 
                   "minimum_amount", "maximum_amount", "icon", "description"]
        )
        
        # Filter by amount if provided
        if amount is not None:
            amount = float(amount)
            payment_methods = [pm for pm in payment_methods if pm.minimum_amount <= amount <= pm.maximum_amount]
        
        # Calculate processing fees
        for method in payment_methods:
            if amount is not None:
                method.processing_fee = method.calculate_processing_fee(amount)
                method.total_amount = amount + method.processing_fee
            else:
                method.processing_fee = 0
                method.total_amount = 0
        
        return {
            "success": True,
            "payment_methods": payment_methods
        }
    
    except Exception as e:
        frappe.log_error(f"Error getting payment methods: {str(e)}", "Payment Methods")
        return {
            "success": False,
            "error": str(e)
        }

@frappe.whitelist()
def enable_payment_method(method_name, enable=True):
    """Enable or disable a payment method"""
    try:
        payment_method = frappe.get_doc("Payment Method", method_name)
        payment_method.enabled = enable
        payment_method.save()
        
        return {
            "success": True,
            "message": _("Payment method {0} {1}").format(
                method_name, 
                "enabled" if enable else "disabled"
            )
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }