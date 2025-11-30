import frappe
from frappe.model.document import Document
from frappe import _

class PaymentGatewaySettings(Document):
    def validate(self):
        self.validate_api_credentials()
        self.validate_webhook_config()
    
    def validate_api_credentials(self):
        """Validate API credentials"""
        if self.gateway_name == "ZoykTech":
            if not self.zoyktech_api_key:
                frappe.throw(_("ZoykTech API Key is required"))
            
            if not self.zoyktech_secret_key:
                frappe.throw(_("ZoykTech Secret Key is required"))
    
    def validate_webhook_config(self):
        """Validate webhook configuration"""
        if not self.webhook_secret:
            frappe.msgprint(_("Webhook secret is not set. Webhook verification will be disabled."), alert=True)
    
    def get_encrypted_api_key(self):
        """Get encrypted API key"""
        return self.get_password('zoyktech_api_key')
    
    def get_encrypted_secret_key(self):
        """Get encrypted secret key"""
        return self.get_password('zoyktech_secret_key')
    
    def get_encrypted_webhook_secret(self):
        """Get encrypted webhook secret"""
        return self.get_password('webhook_secret')

@frappe.whitelist()
def test_gateway_connection():
    """Test connection to payment gateway"""
    try:
        from zoyktech_zambia_payments.zoyktech_zambia_payments.api.zoyktech_client import ZoykTechClient
        
        client = ZoykTechClient()
        
        # Try to get payment methods as a connection test
        payment_methods = client.get_payment_methods()
        
        return {
            "success": True,
            "message": _("Connection test successful"),
            "payment_methods": payment_methods
        }
    
    except Exception as e:
        frappe.log_error(f"Gateway connection test failed: {str(e)}", "Gateway Test")
        return {
            "success": False,
            "message": _("Connection test failed: {0}").format(str(e))
        }

@frappe.whitelist()
def get_gateway_status():
    """Get payment gateway status"""
    try:
        settings = frappe.get_single("Payment Gateway Settings")
        
        return {
            "success": True,
            "gateway_name": settings.gateway_name,
            "is_test_mode": settings.is_test_mode,
            "api_configured": bool(settings.zoyktech_api_key),
            "webhook_configured": bool(settings.get_password('webhook_secret'))
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }