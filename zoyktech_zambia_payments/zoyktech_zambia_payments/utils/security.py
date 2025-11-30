import frappe
import hashlib
import hmac
import base64
from frappe import _
from cryptography.fernet import Fernet
from typing import Optional
import json

def encrypt_data(data: str, key: str = None) -> str:
    """
    Encrypt sensitive data
    
    Args:
        data: Data to encrypt
        key: Encryption key (uses app secret if not provided)
        
    Returns:
        Encrypted data
    """
    try:
        if not key:
            key = frappe.get_site_config().get("encryption_key") or Fernet.generate_key()
        
        fernet = Fernet(base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'\0')))
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
        
    except Exception as e:
        frappe.log_error(f"Encryption error: {str(e)}", "Security Error")
        return data

def decrypt_data(encrypted_data: str, key: str = None) -> str:
    """
    Decrypt sensitive data
    
    Args:
        encrypted_data: Data to decrypt
        key: Decryption key (uses app secret if not provided)
        
    Returns:
        Decrypted data
    """
    try:
        if not key:
            key = frappe.get_site_config().get("encryption_key")
            if not key:
                return encrypted_data
        
        fernet = Fernet(base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b'\0')))
        decrypted_data = fernet.decrypt(base64.urlsafe_b64decode(encrypted_data))
        return decrypted_data.decode()
        
    except Exception as e:
        frappe.log_error(f"Decryption error: {str(e)}", "Security Error")
        return encrypted_data

def hash_sensitive_data(data: str, salt: str = None) -> str:
    """
    Hash sensitive data for storage
    
    Args:
        data: Data to hash
        salt: Salt for hashing
        
    Returns:
        Hashed data
    """
    if not salt:
        salt = frappe.get_site_config().get("hash_salt", "default_salt")
    
    return hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000).hex()

def validate_webhook_origin(ip_address: str) -> bool:
    """
    Validate webhook origin IP address
    
    Args:
        ip_address: IP address to validate
        
    Returns:
        Boolean indicating if origin is valid
    """
    # List of trusted IPs/ranges for ZoykTech
    trusted_ips = [
        '52.31.139.75',
        '52.49.173.169',
        '52.214.14.220',
        '35.156.51.163',
        '35.157.221.52'
    ]
    
    # For now, accept all origins in development
    if frappe.conf.developer_mode:
        return True
    
    return ip_address in trusted_ips

def generate_api_key() -> str:
    """
    Generate secure API key
    
    Returns:
        Generated API key
    """
    import secrets
    return secrets.token_urlsafe(32)

def generate_webhook_secret() -> str:
    """
    Generate webhook secret for signature verification
    
    Returns:
        Generated webhook secret
    """
    import secrets
    return secrets.token_hex(32)

def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging
    
    Args:
        data: Data to mask
        visible_chars: Number of characters to keep visible
        
    Returns:
        Masked data
    """
    if not data or len(data) <= visible_chars:
        return data
    
    visible = data[:visible_chars]
    masked = '*' * (len(data) - visible_chars)
    return visible + masked

def validate_password_strength(password: str) -> bool:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Boolean indicating if password is strong enough
    """
    if len(password) < 8:
        return False
    
    if not any(char.isdigit() for char in password):
        return False
    
    if not any(char.isupper() for char in password):
        return False
    
    if not any(char.islower() for char in password):
        return False
    
    return True

def sanitize_input(data: str) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        data: Input data to sanitize
        
    Returns:
        Sanitized data
    """
    import html
    return html.escape(data.strip())