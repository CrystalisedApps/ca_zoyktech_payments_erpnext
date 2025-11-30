import frappe
from frappe import _
from typing import Optional

def format_currency_zmw(amount: float, include_symbol: bool = True) -> str:
    """
    Format amount as Zambian Kwacha
    
    Args:
        amount: Amount to format
        include_symbol: Whether to include currency symbol
        
    Returns:
        Formatted currency string
    """
    formatted = f"{amount:,.2f}"
    if include_symbol:
        return f"ZMW {formatted}"
    return formatted

def format_phone_zm(phone: str) -> str:
    """
    Format Zambian phone number for display
    
    Args:
        phone: Phone number to format
        
    Returns:
        Formatted phone number
    """
    if not phone:
        return phone
    
    # Remove all non-digit characters
    cleaned = ''.join(filter(str.isdigit, phone))
    
    if cleaned.startswith('260'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('0'):
        cleaned = cleaned[1:]
    
    if len(cleaned) == 9:
        return f"+260 {cleaned[:3]} {cleaned[3:6]} {cleaned[6:]}"
    
    return phone

def format_date_time(dt_string: str, format_type: str = 'short') -> str:
    """
    Format date time string for display
    
    Args:
        dt_string: Date time string
        format_type: Format type (short, long, time)
        
    Returns:
        Formatted date time string
    """
    if not dt_string:
        return ""
    
    from frappe.utils import format_datetime, format_date, format_time
    
    if format_type == 'short':
        return format_date(dt_string)
    elif format_type == 'time':
        return format_time(dt_string)
    else:
        return format_datetime(dt_string)

def format_payment_status(status: str) -> str:
    """
    Format payment status for display with color coding
    
    Args:
        status: Payment status
        
    Returns:
        Formatted status with HTML
    """
    status_colors = {
        'Completed': 'success',
        'Pending': 'warning',
        'Failed': 'danger',
        'Cancelled': 'secondary',
        'Refunded': 'info',
        'Expired': 'secondary'
    }
    
    color = status_colors.get(status, 'secondary')
    return f'<span class="badge badge-{color}">{status}</span>'

def truncate_string(text: str, max_length: int = 50) -> str:
    """
    Truncate string to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string
    """
    if not text:
        return text
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + '...'