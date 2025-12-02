# payment_processor.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import frappe
from frappe import _

class BasePaymentProcessor(ABC):
    """Abstract base class for payment processors"""
    
    @abstractmethod
    def initiate_payment(self, payment_data: Dict) -> Dict:
        """Initiate a payment with the gateway"""
        pass
    
    @abstractmethod
    def verify_payment(self, payment_reference: str) -> Dict:
        """Verify payment status with the gateway"""
        pass
    
    @abstractmethod
    def refund_payment(self, refund_data: Dict) -> Dict:
        """Process refund for a payment"""
        pass
    
    def get_supported_currencies(self) -> List[str]:
        """Get supported currencies"""
        return ['ZMW', 'USD', 'GBP', 'EUR']
    
    def get_supported_payment_methods(self) -> List[str]:
        """Get supported payment methods"""
        return ['card', 'mobile_money', 'bank_transfer', 'mtn', 'airtel']
    
    def format_amount(self, amount: float, currency: str) -> float:
        """Format amount based on currency"""
        if currency == 'ZMW':
            # ZMW typically doesn't have cents
            return round(amount)
        return round(amount, 2)
    
    def validate_payment_data(self, payment_data: Dict) -> bool:
        """Validate payment data before processing"""
        required_fields = ['amount', 'currency', 'reference']
        for field in required_fields:
            if field not in payment_data:
                frappe.throw(_(f"Missing required field: {field}"))
        
        if payment_data['amount'] <= 0:
            frappe.throw(_("Payment amount must be greater than 0"))
        
        return True
    
    def calculate_processing_fee(self, amount: float, payment_method: str = None) -> float:
        """Calculate processing fee for payment"""
        base_fee = 2.0  # ZMW
        
        if payment_method and 'mobile' in payment_method.lower():
            percentage_fee = 0.015  # 1.5%
        else:
            percentage_fee = 0.025  # 2.5%
        
        fee = (amount * percentage_fee) + base_fee
        return min(fee, 50.0)  # Cap at 50 ZMW