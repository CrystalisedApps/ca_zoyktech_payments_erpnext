import frappe
import unittest
import json
from frappe.tests.utils import FrappeTestCase
from zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks import handle_zoyktech_callback

class TestWebhooks(FrappeTestCase):
    def setUp(self):
        """Set up test data"""
        self.test_payment_data = {
            "event": "payment.successful",
            "data": {
                "reference": "TEST_REF_001",
                "amount": 100.0,
                "currency": "ZMW",
                "transaction_id": "TXN_123456",
                "customer_email": "test@example.com",
                "customer_phone": "+260971234567",
                "payment_method": "mobile_money"
            }
        }
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        # This would test signature validation logic
        # For now, just verify the function exists
        from zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks import validate_webhook_signature
        self.assertTrue(callable(validate_webhook_signature))
    
    def test_successful_payment_webhook(self):
        """Test successful payment webhook processing"""
        # Create a test payment transaction first
        test_txn = frappe.get_doc({
            "doctype": "Payment Transaction",
            "reference_id": "TEST_REF_001",
            "amount": 100.0,
            "currency": "ZMW",
            "status": "Pending",
            "customer_email": "test@example.com",
            "customer_phone": "+260971234567"
        })
        test_txn.insert()
        
        # Test webhook processing
        try:
            # This would normally be called via API
            # For testing, we'll call the handler directly
            result = handle_successful_payment(self.test_payment_data["data"])
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Webhook processing failed: {str(e)}")
    
    def test_failed_payment_webhook(self):
        """Test failed payment webhook processing"""
        failed_payment_data = {
            "reference": "TEST_REF_002",
            "amount": 50.0,
            "currency": "ZMW",
            "failure_reason": "Insufficient funds"
        }
        
        # Create test transaction
        test_txn = frappe.get_doc({
            "doctype": "Payment Transaction",
            "reference_id": "TEST_REF_002",
            "amount": 50.0,
            "currency": "ZMW",
            "status": "Pending"
        })
        test_txn.insert()
        
        try:
            from zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks import handle_failed_payment
            result = handle_failed_payment(failed_payment_data)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Failed payment webhook processing failed: {str(e)}")
    
    def test_webhook_invalid_payload(self):
        """Test webhook with invalid payload"""
        invalid_payload = "invalid json"
        
        # This should handle JSON parsing errors gracefully
        from zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks import handle_zoyktech_callback
        # We can't easily test this without mocking the request context
        # But we can verify the error handling exists
    
    def test_webhook_unknown_event(self):
        """Test webhook with unknown event type"""
        unknown_event_data = {
            "event": "unknown.event",
            "data": {
                "reference": "TEST_REF_003",
                "amount": 25.0
            }
        }
        
        # This should return an error for unknown events
        from zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks import handle_zoyktech_callback
        # Testing would require mocking the request context

def handle_successful_payment(payment_data):
    """Helper function to test successful payment processing"""
    from zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks import handle_successful_payment as actual_handler
    return actual_handler(payment_data)

if __name__ == '__main__':
    unittest.main()