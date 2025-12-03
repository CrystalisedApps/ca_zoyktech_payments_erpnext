# payment_gateway_settings.py

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class PaymentGatewaySettings(Document):
    def validate(self):
        """Validate settings"""
        self.validate_api_credentials()
        self.validate_webhook_config()
        self.validate_urls()
        self.validate_payment_methods()
        
        # Update default payment method options
        self.update_default_method_options()
    
    def on_update(self):
        """Clear cache after update"""
        self.clear_cache()
    
    def clear_cache(self):
        """Clear settings cache"""
        frappe.clear_cache(doctype=self.doctype)
        frappe.cache().delete_value(f"singles:{self.doctype}")
        frappe.cache().delete_value("payment_gateway_settings")
    
    def validate_api_credentials(self):
        """Validate API credentials"""
        if self.gateway_name == "ZoykTech":
            if not self.get_password("api_key", raise_exception=False):
                frappe.throw(_("API Key is required"))
            
            if not self.get_password("secret_key", raise_exception=False):
                frappe.throw(_("Secret Key is required"))
    
    def validate_webhook_config(self):
        """Validate webhook configuration"""
        if self.gateway_name == "ZoykTech" and not self.get_password("webhook_secret", raise_exception=False):
            frappe.msgprint(
                _("Webhook secret is not set. Webhook verification will be disabled."),
                alert=True,
                indicator="orange"
            )
    
    def validate_urls(self):
        """Validate URLs"""
        if self.is_test_mode and not self.test_base_url:
            frappe.throw(_("Test Base URL is required when Test Mode is enabled"))
        
        if not self.is_test_mode and self.gateway_name == "ZoykTech" and not self.base_url:
            frappe.throw(_("Base URL is required when not in Test Mode"))
    
    def validate_payment_methods(self):
        """Validate payment methods configuration"""
        if not self.enabled_payment_methods:
            frappe.msgprint(
                _("No payment methods configured. Customers won't be able to make payments."),
                alert=True,
                indicator="red"
            )
    
    def update_default_method_options(self):
        """Update default payment method field options based on enabled methods"""
        if not self.enabled_payment_methods:
            self.default_payment_method = ""
            return
        
        # Get display names of enabled methods
        display_names = []
        for row in self.enabled_payment_methods:
            if not row.payment_method:
                continue
                
            # Get the payment_method field value directly from the child table
            display_names.append(row.payment_method)
        
        # Remove duplicates
        display_names = list(set(display_names))
        
        # If current default is not in enabled methods, clear it
        if self.default_payment_method and self.default_payment_method not in display_names:
            self.default_payment_method = ""
    
    def get_base_url(self):
        """Get appropriate base URL based on mode"""
        if cint(self.is_test_mode):
            return self.test_base_url or "https://sandbox.zoyktech.com"
        return self.base_url or "https://api.zoyktech.com"
    
    def get_enabled_payment_methods_list(self):
        """Get simple list of enabled payment method display names"""
        if not self.enabled_payment_methods:
            return []
        
        methods = []
        for row in self.enabled_payment_methods:
            if row.payment_method and row.enabled:
                methods.append(row.payment_method)
        
        return methods
    
    @property
    def api_key(self):
        """Get encrypted API key"""
        return self.get_password("api_key", raise_exception=False)
    
    @property
    def secret_key(self):
        """Get encrypted secret key"""
        return self.get_password("secret_key", raise_exception=False)
    
    @property
    def webhook_secret_key(self):
        """Get encrypted webhook secret"""
        return self.get_password("webhook_secret", raise_exception=False)


@frappe.whitelist()
def get_default_payment_method_options():
    """Get payment methods for dropdown - dynamic based on enabled methods"""
    try:
        settings = frappe.get_single("Payment Gateway Settings")
        
        if not settings.enabled_payment_methods:
            return ""
        
        # Get payment method values from child table
        display_names = []
        for row in settings.enabled_payment_methods:
            if row.payment_method:
                display_names.append(row.payment_method)
        
        # Remove duplicates and sort
        display_names = sorted(list(set(display_names)))
        
        # Add empty option at the start
        display_names.insert(0, "")
        
        # Return as newline-separated string for Select field
        return "\n".join(display_names)
        
    except Exception as e:
        frappe.log_error(f"Error getting payment method options: {str(e)}")
        return ""


@frappe.whitelist()
def test_gateway_connection():
    """Test connection to payment gateway"""
    try:
        settings = frappe.get_single("Payment Gateway Settings")
        
        # Check if credentials exist
        if not settings.api_key:
            return {
                "success": False,
                "message": _("API Key is not configured")
            }
        
        # Import inside function to avoid circular imports
        from zoyktech_zambia_payments.zoyktech_zambia_payments.api.zoyktech_client import ZoykTechClient
        
        # Initialize client and test connection
        client = ZoykTechClient()
        
        # Test connection
        result = client.test_connection()
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Connection test completed"),
            "details": result
        }
        
    except Exception as e:
        frappe.log_error(
            f"Gateway connection test failed: {str(e)}",
            "Gateway Test"
        )
        return {
            "success": False,
            "message": _("Connection test failed: {0}").format(str(e))
        }


@frappe.whitelist()
def clear_cache():
    """Clear settings cache"""
    try:
        frappe.clear_cache(doctype="Payment Gateway Settings")
        frappe.cache().delete_value(f"singles:Payment Gateway Settings")
        
        return {"success": True, "message": _("Cache cleared successfully")}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def sync_payment_methods():
    """Sync payment methods from Payment Method doctype"""
    try:
        # Get all payment method options from the Payment Method child table's select field
        # We need to get unique payment_method values
        payment_method_options = [
            "MTN Mobile Money",
            "Airtel Money", 
            "Visa Card",
            "MasterCard",
            "Bank Transfer",
            "Zanaco",
            "Stanbic",
            "FNB"
        ]
        
        # Get or create settings
        if frappe.db.exists("Payment Gateway Settings", "Payment Gateway Settings"):
            settings = frappe.get_doc("Payment Gateway Settings", "Payment Gateway Settings")
        else:
            settings = frappe.new_doc("Payment Gateway Settings")
        
        # Clear existing methods
        settings.enabled_payment_methods = []
        
        # Add all payment methods
        for method in payment_method_options:
            row = settings.append("enabled_payment_methods", {})
            row.payment_method = method
            row.enabled = 1
            row.payment_gateway = "ZoykTech"
            row.processing_fee_percentage = 2.5
            row.fixed_fee = 2.0
            row.minimum_amount = 1.0
            row.maximum_amount = 50000.0
        
        # Clear default payment method to avoid errors
        settings.default_payment_method = ""
        
        settings.save()
        frappe.db.commit()
        
        # Clear cache
        clear_cache()
        
        return {
            "success": True,
            "message": _("Synced {0} payment methods").format(len(payment_method_options)),
            "count": len(payment_method_options)
        }
        
    except Exception as e:
        frappe.log_error(f"Failed to sync payment methods: {str(e)}")
        return {
            "success": False, 
            "message": _("Failed to sync: {0}").format(str(e))
        }


@frappe.whitelist()
def get_configured_methods():
    """Get configured payment methods with details"""
    try:
        settings = frappe.get_single("Payment Gateway Settings")
        
        if not settings.enabled_payment_methods:
            return {
                "success": True,
                "methods": [],
                "count": 0
            }
        
        methods = []
        for row in settings.enabled_payment_methods:
            methods.append({
                "name": row.name,
                "payment_method": row.payment_method,
                "payment_gateway": row.payment_gateway or "ZoykTech",
                "processing_fee_percentage": flt(row.processing_fee_percentage or 0),
                "fixed_fee": flt(row.fixed_fee or 0),
                "minimum_amount": flt(row.minimum_amount or 0),
                "maximum_amount": flt(row.maximum_amount or 0),
                "icon": row.icon if hasattr(row, 'icon') else "",
                "description": row.description if hasattr(row, 'description') else ""
            })
        
        return {
            "success": True,
            "methods": methods,
            "count": len(methods)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting configured methods: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_settings_summary():
    """Get settings summary"""
    try:
        settings = frappe.get_single("Payment Gateway Settings")
        
        # Get default method display name
        default_method_display = settings.default_payment_method or ""
        
        return {
            "success": True,
            "gateway_name": settings.gateway_name,
            "is_test_mode": cint(settings.is_test_mode),
            "configured_methods": len(settings.enabled_payment_methods) if settings.enabled_payment_methods else 0,
            "default_method": default_method_display,
            "payment_link_expiry_days": settings.payment_link_expiry_days or 0,
            "payment_link_expiry_hours": settings.payment_link_expiry_hours or 0,
            "auto_create_links": cint(settings.auto_create_payment_links),
            "email_notifications": cint(settings.enable_email_notifications),
            "sms_notifications": cint(settings.enable_sms_notifications)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def get_all_payment_methods():
    """Get all payment method options"""
    try:
        # These are the options from the Payment Method child table's select field
        options = [
            "",
            "MTN Mobile Money",
            "Airtel Money",
            "Visa Card",
            "MasterCard",
            "Bank Transfer",
            "Zanaco",
            "Stanbic",
            "FNB"
        ]
        
        return {
            "success": True,
            "options": "\n".join(options)
        }
        
    except Exception as e:
        frappe.log_error(f"Error getting all payment methods: {str(e)}")
        return {
            "success": False,
            "options": ""
        }