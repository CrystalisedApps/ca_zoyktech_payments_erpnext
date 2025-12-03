import hashlib
import hmac
import json
import time
from typing import Dict, List, Optional, Tuple

import frappe
import requests
from frappe import _

from ..utils.helpers import format_zambian_phone_number, validate_zambian_phone_number
from ..utils.security import decrypt_data, encrypt_data


class ZoykTechClient:
    """Complete ZoykTech Payment Gateway Client Implementation"""

    def __init__(self, settings=None):
        self.settings = settings or self.get_settings()
        self.base_url = self.get_base_url()
        self.headers = self.get_headers()
        self.timeout = 30

    def get_settings(self):
        """Get payment gateway settings with validation"""
        try:
            settings = frappe.get_single("Payment Gateway Settings")
            if not settings.get_password("api_key", raise_exception=False):  # CHANGED
                frappe.throw(_("API Key is not configured in Payment Gateway Settings"))
            return settings
        except Exception as e:
            frappe.log_error(f"Error getting payment settings: {str(e)}", "Payment Settings Error")
            frappe.throw(_("Payment gateway settings not found. Please configure them first."))

    def get_base_url(self):
        """Get base URL based on test mode"""
        if self.settings.is_test_mode:
            return self.settings.test_base_url or "https://sandbox.zoyktech.com"
        return self.settings.base_url or "https://api.zoyktech.com"

    def get_headers(self):
        """Get request headers with authentication"""
        api_key = self.settings.get_password("api_key")  # CHANGED
        
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "ZoykTechZambiaPayments/0.0.1",
        }

    def test_connection(self) -> Dict:
        """
        Test connection to ZoykTech API
        
        Returns:
            Test connection response
        """
        try:
            # Try to connect to a simple endpoint
            endpoint = f"{self.base_url}/api/v1/payment-methods"
            
            response = requests.get(
                endpoint, 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Connection successful",
                    "status_code": response.status_code,
                    "base_url": self.base_url,
                    "test_mode": self.settings.is_test_mode
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "message": "Authentication failed. Invalid API Key.",
                    "status_code": response.status_code,
                    "base_url": self.base_url
                }
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", f"Status: {response.status_code}")
                except:
                    error_msg = f"Status: {response.status_code}"
                
                return {
                    "success": False,
                    "message": error_msg,
                    "status_code": response.status_code,
                    "base_url": self.base_url
                }
                
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": f"Could not connect to {self.base_url}. Please check the URL.",
                "base_url": self.base_url
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Connection timeout. Server is not responding.",
                "base_url": self.base_url
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Connection error: {str(e)}",
                "base_url": self.base_url
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "base_url": self.base_url
            }

    def initiate_payment(self, payment_data: Dict) -> Dict:
        """
        Initiate a payment with ZoykTech

        Args:
            payment_data: Dictionary containing payment details

        Returns:
            Payment initiation response
        """
        endpoint = f"{self.base_url}/api/v1/payments/initiate"

        # Validate required fields
        self.validate_payment_data(payment_data)

        # Prepare payload
        payload = self.prepare_payment_payload(payment_data)

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=self.timeout)

            return self.handle_response(response, "initiate_payment")

        except requests.exceptions.Timeout:
            frappe.log_error("ZoykTech API timeout", "Payment Timeout")
            frappe.throw(_("Payment gateway timeout. Please try again."))
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"ZoykTech API Error: {str(e)}", "Payment API Error")
            frappe.throw(_("Failed to initiate payment. Please try again."))

    def validate_payment_data(self, payment_data: Dict):
        """Validate payment data before sending to gateway"""
        required_fields = ["amount", "currency", "customer_email", "customer_phone", "reference"]
        for field in required_fields:
            if field not in payment_data:
                frappe.throw(_(f"Missing required field: {field}"))

        if payment_data["amount"] <= 0:
            frappe.throw(_("Payment amount must be greater than 0"))

        # Validate phone number
        if not validate_zambian_phone_number(payment_data["customer_phone"]):
            frappe.throw(_("Invalid Zambian phone number format"))

    def prepare_payment_payload(self, payment_data: Dict) -> Dict:
        """Prepare payload for payment initiation"""
        payload = {
            "amount": float(payment_data["amount"]),
            "currency": payment_data.get("currency", "ZMW"),
            "customer_email": payment_data["customer_email"],
            "customer_phone": format_zambian_phone_number(payment_data["customer_phone"]),
            "reference": payment_data["reference"],
            "callback_url": payment_data.get("callback_url", self.get_default_callback_url()),
            "metadata": payment_data.get("metadata", {}),
        }

        # Add payment method if specified
        if payment_data.get("payment_method"):
            payload["payment_method"] = payment_data["payment_method"]

        return payload

    def verify_payment(self, payment_reference: str) -> Dict:
        """
        Verify payment status

        Args:
            payment_reference: The payment reference to verify

        Returns:
            Payment verification response
        """
        endpoint = f"{self.base_url}/api/v1/payments/verify/{payment_reference}"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
            return self.handle_response(response, "verify_payment")
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"ZoykTech Verification Error: {str(e)}", "Payment Verification Error")
            frappe.throw(_("Failed to verify payment status."))

    def create_payment_intent(self, intent_data: Dict) -> Dict:
        """
        Create a payment intent for card payments

        Args:
            intent_data: Payment intent data

        Returns:
            Payment intent response
        """
        endpoint = f"{self.base_url}/api/v1/payments/intent"

        payload = {
            "amount": float(intent_data["amount"]),
            "currency": intent_data.get("currency", "ZMW"),
            "payment_method": intent_data.get("payment_method", "card"),
            "customer_email": intent_data["customer_email"],
            "customer_phone": format_zambian_phone_number(intent_data.get("customer_phone", "")),
            "reference": intent_data["reference"],
            "metadata": intent_data.get("metadata", {}),
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=self.timeout)
            return self.handle_response(response, "create_payment_intent")
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"ZoykTech Intent Error: {str(e)}", "Payment Intent Error")
            frappe.throw(_("Failed to create payment intent."))

    def process_mobile_money(self, mobile_data: Dict) -> Dict:
        """
        Process mobile money payment

        Args:
            mobile_data: Mobile money payment data

        Returns:
            Mobile money payment response
        """
        endpoint = f"{self.base_url}/api/v1/payments/mobile-money"

        self.validate_mobile_money_data(mobile_data)

        payload = {
            "amount": float(mobile_data["amount"]),
            "currency": mobile_data.get("currency", "ZMW"),
            "network": mobile_data["network"].lower(),  # mtn, airtel
            "phone_number": format_zambian_phone_number(mobile_data["phone_number"]),
            "reference": mobile_data["reference"],
            "customer_email": mobile_data.get("customer_email"),
            "customer_name": mobile_data.get("customer_name"),
            "metadata": mobile_data.get("metadata", {}),
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=self.timeout)
            return self.handle_response(response, "process_mobile_money")
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"ZoykTech Mobile Money Error: {str(e)}", "Mobile Money Error")
            frappe.throw(_("Failed to process mobile money payment."))

    def validate_mobile_money_data(self, mobile_data: Dict):
        """Validate mobile money payment data"""
        required_fields = ["amount", "network", "phone_number", "reference"]
        for field in required_fields:
            if field not in mobile_data:
                frappe.throw(_(f"Missing required field for mobile money: {field}"))

        valid_networks = ["mtn", "airtel"]
        if mobile_data["network"].lower() not in valid_networks:
            frappe.throw(_(f"Invalid network. Must be one of: {', '.join(valid_networks)}"))

    def refund_payment(self, refund_data: Dict) -> Dict:
        """
        Process refund for a payment

        Args:
            refund_data: Refund data

        Returns:
            Refund response
        """
        endpoint = f"{self.base_url}/api/v1/payments/refund"

        payload = {
            "transaction_id": refund_data["transaction_id"],
            "amount": float(refund_data.get("amount", 0)),
            "reason": refund_data.get("reason", "Customer request"),
            "reference": refund_data.get("reference", f"refund_{int(time.time())}"),
        }

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=self.timeout)
            return self.handle_response(response, "refund_payment")
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"ZoykTech Refund Error: {str(e)}", "Refund Error")
            frappe.throw(_("Failed to process refund."))

    def handle_response(self, response: requests.Response, operation: str) -> Dict:
        """Handle API response with proper error handling"""
        try:
            response_data = response.json()
        except ValueError:
            frappe.log_error(f"Invalid JSON response: {response.text}", f"{operation} Error")
            frappe.throw(_("Invalid response from payment gateway"))

        if response.status_code == 200:
            return response_data
        else:
            error_message = response_data.get("message", "Unknown error occurred")
            frappe.log_error(f"ZoykTech {operation} failed: {error_message}", f"{operation} Error")
            frappe.throw(_(f"Payment gateway error: {error_message}"))

    def get_default_callback_url(self) -> str:
        """Get default callback URL for webhooks"""
        site_url = frappe.utils.get_url()
        return f"{site_url}/api/method/zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks.handle_zoyktech_callback"

    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Validate webhook signature

        Args:
            payload: Raw payload string
            signature: Signature from header

        Returns:
            Boolean indicating if signature is valid
        """
        secret = self.settings.get_password("webhook_secret")
        if not secret:
            frappe.log_error("Webhook secret not configured", "Webhook Validation")
            return False

        computed_signature = hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature)

    def get_payment_methods(self) -> List[Dict]:
        """Get available payment methods from ZoykTech"""
        endpoint = f"{self.base_url}/api/v1/payment-methods"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=self.timeout)
            return self.handle_response(response, "get_payment_methods")
        except requests.exceptions.RequestException as e:
            frappe.log_error(f"ZoykTech Payment Methods Error: {str(e)}", "Payment Methods Error")
            return []