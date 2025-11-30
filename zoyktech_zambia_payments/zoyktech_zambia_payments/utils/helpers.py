import frappe
import re
import random
import string
from frappe import _
from typing import Dict, Optional, List
from datetime import datetime, timedelta

def validate_zambian_phone_number(phone: str) -> bool:
    """
    Validate Zambian phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Boolean indicating if phone is valid
    """
    if not phone:
        return False
    
    # Remove any whitespace and special characters
    cleaned_phone = re.sub(r'[\s+\-()]', '', phone)
    
    # Zambian phone number patterns
    patterns = [
        r'^\+260(76|77|96|97)\d{7}$',  # International format
        r'^260(76|77|96|97)\d{7}$',    # Without +
        r'^0(76|77|96|97)\d{7}$',      # Local format
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned_phone):
            return True
    
    return False

def format_zambian_phone_number(phone: str) -> str:
    """
    Format phone number to international format
    
    Args:
        phone: Phone number to format
        
    Returns:
        Formatted phone number in international format
    """
    if not phone:
        return phone
    
    # Remove any non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # If it starts with 0, convert to +260
    if cleaned.startswith('0'):
        cleaned = '+260' + cleaned[1:]
    elif cleaned.startswith('260') and not cleaned.startswith('+260'):
        cleaned = '+' + cleaned
    elif not cleaned.startswith('+'):
        cleaned = '+260' + cleaned
    
    return cleaned

def generate_transaction_reference(prefix: str = "TXN") -> str:
    """
    Generate unique transaction reference
    
    Args:
        prefix: Reference prefix
        
    Returns:
        Unique transaction reference
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}_{timestamp}_{random_str}"

def get_payment_gateway_settings() -> Dict:
    """
    Get payment gateway settings
    
    Returns:
        Dictionary of payment gateway settings
    """
    try:
        settings = frappe.get_single("Payment Gateway Settings")
        return {
            'gateway_name': settings.gateway_name,
            'is_test_mode': settings.is_test_mode,
            'enabled_methods': [method.payment_method for method in settings.enabled_payment_methods],
            'api_key_configured': bool(settings.zoyktech_api_key),
            'webhook_secret_configured': bool(settings.get_password('webhook_secret'))
        }
    except Exception as e:
        frappe.log_error(f"Error getting payment settings: {str(e)}", "Payment Settings")
        return {}

def format_currency_zmw(amount: float) -> str:
    """
    Format amount as Zambian Kwacha
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted currency string
    """
    return f"ZMW {amount:,.2f}"

def calculate_transaction_fee(amount: float, payment_method: str = None) -> float:
    """
    Calculate transaction fee based on amount and payment method
    
    Args:
        amount: Transaction amount
        payment_method: Payment method used
        
    Returns:
        Transaction fee
    """
    base_fee = 2.0  # Base fee in ZMW
    
    if payment_method and 'mobile' in payment_method.lower():
        # Mobile money typically has higher fees
        percentage_fee = 0.015  # 1.5%
    else:
        percentage_fee = 0.025  # 2.5% for cards
    
    fee = (amount * percentage_fee) + base_fee
    return min(fee, 50.0)  # Cap at 50 ZMW

def is_business_hours() -> bool:
    """
    Check if current time is within business hours (8 AM to 5 PM)
    
    Returns:
        Boolean indicating if it's business hours
    """
    now = datetime.now()
    return 8 <= now.hour < 17

def get_supported_currencies() -> List[str]:
    """
    Get list of supported currencies
    
    Returns:
        List of currency codes
    """
    return ['ZMW', 'USD', 'GBP', 'EUR']

def create_payment_reference(doctype: str, docname: str) -> str:
    """
    Create unique payment reference for document
    
    Args:
        doctype: Document type
        docname: Document name
        
    Returns:
        Unique payment reference
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    doc_short = doctype[:3].upper()
    return f"{doc_short}_{docname}_{timestamp}"

def get_customer_payment_history(customer: str, limit: int = 10) -> List[Dict]:
    """
    Get customer payment history
    
    Args:
        customer: Customer name
        limit: Number of records to return
        
    Returns:
        List of payment transactions
    """
    payments = frappe.get_all("Payment Transaction",
        filters={
            "customer_email": ["like", f"%{customer}%"]
        },
        fields=["name", "reference_id", "amount", "currency", "status", "payment_method", "payment_completed"],
        order_by="payment_completed desc",
        limit=limit
    )
    
    return payments

def send_payment_notification(reference_id: str, notification_type: str):
    """
    Send payment notification
    
    Args:
        reference_id: Payment reference
        notification_type: Type of notification
    """
    try:
        payment_txn = frappe.get_doc("Payment Transaction", reference_id)
        
        if notification_type == "success":
            subject = _("Payment Successful - {0}").format(reference_id)
            message = _("Your payment of {0} {1} has been processed successfully.").format(
                payment_txn.amount, payment_txn.currency
            )
        elif notification_type == "failure":
            subject = _("Payment Failed - {0}").format(reference_id)
            message = _("Your payment of {0} {1} has failed. Please try again.").format(
                payment_txn.amount, payment_txn.currency
            )
        else:
            return
        
        if payment_txn.customer_email:
            frappe.sendmail(
                recipients=payment_txn.customer_email,
                subject=subject,
                message=message
            )
            
    except Exception as e:
        frappe.log_error(f"Error sending payment notification: {str(e)}", "Notification Error")

def log_payment_activity(reference_id: str, activity: str, details: Dict = None):
    """
    Log payment activity for audit trail
    
    Args:
        reference_id: Payment reference
        activity: Activity description
        details: Additional details
    """
    try:
        activity_log = frappe.new_doc("Activity Log")
        activity_log.reference_doctype = "Payment Transaction"
        activity_log.reference_name = reference_id
        activity_log.subject = activity
        activity_log.operation = "Payment"
        activity_log.content = str(details) if details else ""
        activity_log.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error logging payment activity: {str(e)}", "Activity Log Error")