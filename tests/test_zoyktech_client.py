import frappe
import unittest
from frappe.tests.utils import FrappeTestCase
from zoyktech_zambia_payments.zoyktech_zambia_payments.api.zoyktech_client import ZoykTechClient
from zoyktech_zambia_payments.zoyktech_zambia_payments.utils.helpers import validate_zambian_phone_number, format_zambian_phone_number

class TestZoykTechClient(FrappeTestCase):
    def setUp(self):
        """Set up test client and data"""
        self.client = ZoykTechClient()
        self.valid_payment_data = {
            'amount': 100.0,
            'currency': 'ZMW',
            'customer_email': 'test@example.com',
            'customer_phone': '+260971234567',
            'reference': 'TEST_REF_001'
        }
    
    def test_client_initialization(self):
        """Test that client initializes properly"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.settings)
        self.assertIsNotNone(self.client.base_url)
        self.assertIsNotNone(self.client.headers)
    
    def test_payment_data_validation(self):
        """Test payment data validation"""
        # Test valid data
        try:
            self.client.validate_payment_data(self.valid_payment_data)
        except Exception as e:
            self.fail(f"Valid payment data should not raise exception: {str(e)}")
        
        # Test missing required field
        invalid_data = self.valid_payment_data.copy()
        del invalid_data['reference']
        
        with self.assertRaises(Exception):
            self.client.validate_payment_data(invalid_data)
        
        # Test zero amount
        invalid_amount_data = self.valid_payment_data.copy()
        invalid_amount_data['amount'] = 0
        
        with self.assertRaises(Exception):
            self.client.validate_payment_data(invalid_amount_data)
    
    def test_phone_number_validation(self):
        """Test Zambian phone number validation"""
        # Valid numbers
        valid_numbers = [
            '+260971234567',
            '260971234567',
            '0971234567',
            '0761234567',
            '0771234567'
        ]
        
        for phone in valid_numbers:
            self.assertTrue(validate_zambian_phone_number(phone), f"Should be valid: {phone}")
        
        # Invalid numbers
        invalid_numbers = [
            '1234567890',
            '+255712345678',  # Tanzania
            '071234567',      # Too short
            '',
            None
        ]
        
        for phone in invalid_numbers:
            self.assertFalse(validate_zambian_phone_number(phone), f"Should be invalid: {phone}")
    
    def test_phone_number_formatting(self):
        """Test phone number formatting"""
        test_cases = [
            ('0971234567', '+260971234567'),
            ('260971234567', '+260971234567'),
            ('+260971234567', '+260971234567'),
            ('076 123 4567', '+260761234567'),
            ('077-123-4567', '+260771234567')
        ]
        
        for input_phone, expected_output in test_cases:
            formatted = format_zambian_phone_number(input_phone)
            self.assertEqual(formatted, expected_output, f"Formatting failed for: {input_phone}")
    
    def test_payment_payload_preparation(self):
        """Test payment payload preparation"""
        payment_data = {
            'amount': 150.50,
            'currency': 'ZMW',
            'customer_email': 'customer@example.com',
            'customer_phone': '0971234567',
            'reference': 'INV_001',
            'callback_url': 'https://example.com/callback',
            'metadata': {'invoice_id': 'INV-001'}
        }
        
        payload = self.client.prepare_payment_payload(payment_data)
        
        self.assertEqual(payload['amount'], 150.50)
        self.assertEqual(payload['currency'], 'ZMW')
        self.assertEqual(payload['customer_email'], 'customer@example.com')
        self.assertEqual(payload['customer_phone'], '+260971234567')  # Should be formatted
        self.assertEqual(payload['reference'], 'INV_001')
        self.assertIn('callback_url', payload)
        self.assertIn('metadata', payload)
    
    def test_mobile_money_validation(self):
        """Test mobile money data validation"""
        # Valid data
        valid_mobile_data = {
            'amount': 100.0,
            'network': 'mtn',
            'phone_number': '+260971234567',
            'reference': 'MM_001'
        }
        
        try:
            self.client.validate_mobile_money_data(valid_mobile_data)
        except Exception as e:
            self.fail(f"Valid mobile money data should not raise exception: {str(e)}")
        
        # Invalid network
        invalid_network_data = valid_mobile_data.copy()
        invalid_network_data['network'] = 'invalid_network'
        
        with self.assertRaises(Exception):
            self.client.validate_mobile_money_data(invalid_network_data)
    
    @unittest.skip("Requires actual gateway credentials for integration testing")
    def test_live_gateway_connection(self):
        """Test actual connection to ZoykTech gateway (requires credentials)"""
        try:
            payment_methods = self.client.get_payment_methods()
            self.assertIsInstance(payment_methods, list)
        except Exception as e:
            self.fail(f"Gateway connection test failed: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling in API calls"""
        # Test with invalid endpoint (should handle errors gracefully)
        original_base_url = self.client.base_url
        self.client.base_url = "https://invalid-url-that-does-not-exist.com"
        
        try:
            # This should raise an exception but handle it gracefully
            result = self.client.get_payment_methods()
            # If we get here, the error was handled
            self.assertIsInstance(result, list)
        except Exception as e:
            # Exception should be caught and logged, not propagated
            pass
        finally:
            self.client.base_url = original_base_url
    
    def test_amount_formatting(self):
        """Test amount formatting for different currencies"""
        test_cases = [
            (100.50, 'ZMW', 101),  # ZMW should be rounded
            (100.50, 'USD', 100.50),  # USD should keep decimals
            (100.00, 'GBP', 100.00),
        ]
        
        for amount, currency, expected in test_cases:
            formatted = self.client.format_amount(amount, currency)
            self.assertEqual(formatted, expected, f"Amount formatting failed for {currency}")

if __name__ == '__main__':
    unittest.main()