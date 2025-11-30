import frappe
import re
from frappe import _
from typing import Optional

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email to validate
        
    Returns:
        Boolean indicating if email is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_amount(amount: float, min_amount: float = 1.0, max_amount: float = 100000.0) -> bool:
    """
    Validate payment amount
    
    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount
        
    Returns:
        Boolean indicating if amount is valid
    """
    return min_amount <= amount <= max_amount

def validate_currency(currency: str) -> bool:
    """
    Validate currency code
    
    Args:
        currency: Currency code to validate
        
    Returns:
        Boolean indicating if currency is valid
    """
    valid_currencies = ['ZMW', 'USD', 'GBP', 'EUR']
    return currency.upper() in valid_currencies

def validate_payment_method(method: str) -> bool:
    """
    Validate payment method
    
    Args:
        method: Payment method to validate
        
    Returns:
        Boolean indicating if method is valid
    """
    valid_methods = ['card', 'mobile_money', 'bank_transfer', 'mtn', 'airtel']
    return method.lower() in valid_methods

def validate_api_credentials(api_key: str, secret_key: str) -> bool:
    """
    Validate API credentials format
    
    Args:
        api_key: API key to validate
        secret_key: Secret key to validate
        
    Returns:
        Boolean indicating if credentials are valid
    """
    # Basic validation - adjust based on gateway requirements
    if not api_key or not secret_key:
        return False
    
    if len(api_key) < 10 or len(secret_key) < 10:
        return False
    
    return True

def validate_webhook_url(url: str) -> bool:
    """
    Validate webhook URL
    
    Args:
        url: Webhook URL to validate
        
    Returns:
        Boolean indicating if URL is valid
    """
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def validate_bank_account_number(account_number: str, bank_code: str = None) -> bool:
    """
    Validate bank account number (basic validation)
    
    Args:
        account_number: Account number to validate
        bank_code: Bank code for specific validation
        
    Returns:
        Boolean indicating if account number is valid
    """
    if not account_number or len(account_number) < 5:
        return False
    
    # Remove spaces and special characters
    cleaned = re.sub(r'[^\d]', '', account_number)
    
    return len(cleaned) >= 5 and cleaned.isdigit()