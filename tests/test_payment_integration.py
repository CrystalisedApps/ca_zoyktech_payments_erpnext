import frappe
import unittest
from frappe.tests.utils import FrappeTestCase
from zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration import PaymentIntegration
from zoyktech_zambia_payments.zoyktech_zambia_payments.api.zoyktech_client import ZoykTechClient
from zoyktech_zambia_payments.zoyktech_zambia_payments.utils.helpers import validate_zambian_phone_number, format_zambian_phone_number

class TestPaymentIntegration(FrappeTestCase):
    def setUp(self):
        """Set up test data"""
        self.test_customer = create_test_customer()
        self.test_supplier = create_test_supplier()
        self.test_sales_invoice = create_test_sales_invoice(self.test_customer)
        self.test_purchase_invoice = create_test_purchase_invoice(self.test_supplier)
    
    def tearDown(self):
        """Clean up test data"""
        frappe.db.rollback()
    
    def test_validate_zambian_phone_number(self):
        """Test Zambian phone number validation"""
        # Valid numbers
        self.assertTrue(validate_zambian_phone_number('+260971234567'))
        self.assertTrue(validate_zambian_phone_number('260971234567'))
        self.assertTrue(validate_zambian_phone_number('0971234567'))
        self.assertTrue(validate_zambian_phone_number('0761234567'))
        self.assertTrue(validate_zambian_phone_number('0771234567'))
        self.assertTrue(validate_zambian_phone_number('0961234567'))
        self.assertTrue(validate_zambian_phone_number('0971234567'))
        
        # Invalid numbers
        self.assertFalse(validate_zambian_phone_number('1234567890'))
        self.assertFalse(validate_zambian_phone_number('+255712345678'))  # Tanzania
        self.assertFalse(validate_zambian_phone_number('071234567'))  # Too short
        self.assertFalse(validate_zambian_phone_number(''))
        self.assertFalse(validate_zambian_phone_number(None))
    
    def test_format_zambian_phone_number(self):
        """Test phone number formatting"""
        self.assertEqual(format_zambian_phone_number('0971234567'), '+260971234567')
        self.assertEqual(format_zambian_phone_number('260971234567'), '+260971234567')
        self.assertEqual(format_zambian_phone_number('+260971234567'), '+260971234567')
        self.assertEqual(format_zambian_phone_number('076 123 4567'), '+260761234567')
        self.assertEqual(format_zambian_phone_number('077-123-4567'), '+260771234567')
    
    def test_payment_integration_initialization(self):
        """Test payment integration initialization"""
        integration = PaymentIntegration()
        self.assertIsNotNone(integration)
        self.assertIsNotNone(integration.client)
        self.assertIsNotNone(integration.settings)
    
    def test_create_payment_reference(self):
        """Test payment reference generation"""
        integration = PaymentIntegration()
        reference = integration.generate_payment_reference('Sales Invoice', 'TEST-INV-001')
        
        self.assertIsNotNone(reference)
        self.assertIn('SINV_TEST-INV-001', reference)
        self.assertTrue(len(reference) > 10)
    
    def test_validate_document_for_payment(self):
        """Test document validation for payments"""
        integration = PaymentIntegration()
        
        # Test valid sales invoice
        doc = frappe.get_doc('Sales Invoice', self.test_sales_invoice)
        self.assertTrue(integration.validate_document_for_payment('Sales Invoice', doc))
        
        # Test invalid document type
        with self.assertRaises(Exception):
            integration.validate_document_for_payment('Invalid DocType', doc)
    
    def test_get_payable_amount(self):
        """Test payable amount calculation"""
        integration = PaymentIntegration()
        
        # Sales Invoice
        doc = frappe.get_doc('Sales Invoice', self.test_sales_invoice)
        amount = integration.get_payable_amount('Sales Invoice', doc)
        self.assertEqual(amount, doc.outstanding_amount)
        
        # Purchase Invoice  
        doc = frappe.get_doc('Purchase Invoice', self.test_purchase_invoice)
        amount = integration.get_payable_amount('Purchase Invoice', doc)
        self.assertEqual(amount, doc.outstanding_amount)
    
    def test_payment_link_creation(self):
        """Test payment link creation"""
        integration = PaymentIntegration()
        
        result = integration.create_payment_link(
            'Sales Invoice', 
            self.test_sales_invoice,
            'TEST_REF_001',
            frappe.get_doc('Sales Invoice', self.test_sales_invoice)
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(frappe.db.exists('Payment Link', result))
    
    def test_payment_data_preparation(self):
        """Test payment data preparation"""
        integration = PaymentIntegration()
        doc = frappe.get_doc('Sales Invoice', self.test_sales_invoice)
        
        payment_data = integration.prepare_payment_data(
            'Sales Invoice', 
            doc, 
            'TEST_REF_001',
            'mobile_money'
        )
        
        self.assertIsNotNone(payment_data)
        self.assertEqual(payment_data['amount'], doc.outstanding_amount)
        self.assertEqual(payment_data['currency'], doc.currency)
        self.assertEqual(payment_data['reference'], 'TEST_REF_001')
        self.assertIn('metadata', payment_data)
    
    @unittest.skip("Requires actual gateway credentials")
    def test_payment_creation_with_gateway(self):
        """Test payment creation with actual gateway (requires credentials)"""
        integration = PaymentIntegration()
        
        result = integration.create_payment_request(
            'Sales Invoice',
            self.test_sales_invoice,
            'mobile_money'
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result.get('success') in [True, False])
        
        if result.get('success'):
            self.assertIn('reference_id', result)
            self.assertIn('payment_url', result)
    
    def test_payment_status_check(self):
        """Test payment status checking"""
        integration = PaymentIntegration()
        
        # Test with invalid reference
        result = integration.get_payment_status('INVALID_REFERENCE')
        self.assertIsNotNone(result)
        self.assertIn('success', result)
    
    def test_payment_cancellation(self):
        """Test payment cancellation"""
        integration = PaymentIntegration()
        
        # Create a test payment link first
        payment_link = frappe.get_doc({
            'doctype': 'Payment Link',
            'reference_id': 'TEST_CANCEL_001',
            'linked_doctype': 'Sales Invoice',
            'linked_docname': self.test_sales_invoice,
            'amount': 100.0,
            'currency': 'ZMW',
            'status': 'Pending'
        })
        payment_link.insert()
        
        result = integration.cancel_payment_request('TEST_CANCEL_001')
        self.assertTrue(result.get('success'))
        
        # Verify status was updated
        updated_link = frappe.get_doc('Payment Link', payment_link.name)
        self.assertEqual(updated_link.status, 'Cancelled')

class TestZoykTechClient(FrappeTestCase):
    def setUp(self):
        """Set up test client"""
        self.client = ZoykTechClient()
    
    def test_client_initialization(self):
        """Test client initialization"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.settings)
        self.assertIsNotNone(self.client.base_url)
        self.assertIsNotNone(self.client.headers)
    
    def test_payment_data_validation(self):
        """Test payment data validation"""
        # Valid data
        valid_data = {
            'amount': 100.0,
            'currency': 'ZMW',
            'customer_email': 'test@example.com',
            'customer_phone': '+260971234567',
            'reference': 'TEST_001'
        }
        
        # Should not raise exception
        self.client.validate_payment_data(valid_data)
        
        # Invalid data - missing required field
        invalid_data = {
            'amount': 100.0,
            'currency': 'ZMW',
            'customer_email': 'test@example.com'
            # missing customer_phone and reference
        }
        
        with self.assertRaises(Exception):
            self.client.validate_payment_data(invalid_data)
        
        # Invalid data - zero amount
        invalid_amount_data = {
            'amount': 0,
            'currency': 'ZMW', 
            'customer_email': 'test@example.com',
            'customer_phone': '+260971234567',
            'reference': 'TEST_001'
        }
        
        with self.assertRaises(Exception):
            self.client.validate_payment_data(invalid_amount_data)
    
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
        valid_data = {
            'amount': 100.0,
            'network': 'mtn',
            'phone_number': '+260971234567',
            'reference': 'MM_001'
        }
        
        # Should not raise exception
        self.client.validate_mobile_money_data(valid_data)
        
        # Invalid network
        invalid_network_data = {
            'amount': 100.0,
            'network': 'invalid_network',
            'phone_number': '+260971234567', 
            'reference': 'MM_001'
        }
        
        with self.assertRaises(Exception):
            self.client.validate_mobile_money_data(invalid_network_data)

def create_test_customer():
    """Create test customer"""
    if not frappe.db.exists('Customer', 'Test Customer ZM'):
        customer = frappe.get_doc({
            'doctype': 'Customer',
            'customer_name': 'Test Customer ZM',
            'customer_type': 'Individual',
            'territory': 'Zambia'
        })
        customer.insert()
        return customer.name
    return 'Test Customer ZM'

def create_test_supplier():
    """Create test supplier"""
    if not frappe.db.exists('Supplier', 'Test Supplier ZM'):
        supplier = frappe.get_doc({
            'doctype': 'Supplier',
            'supplier_name': 'Test Supplier ZM',
            'supplier_type': 'Local',
            'country': 'Zambia'
        })
        supplier.insert()
        return supplier.name
    return 'Test Supplier ZM'

def create_test_sales_invoice(customer):
    """Create test sales invoice"""
    invoice = frappe.get_doc({
        'doctype': 'Sales Invoice',
        'customer': customer,
        'due_date': frappe.utils.nowdate(),
        'items': [{
            'item_code': 'Test Item',
            'qty': 1,
            'rate': 1000
        }]
    })
    invoice.insert()
    invoice.submit()
    return invoice.name

def create_test_purchase_invoice(supplier):
    """Create test purchase invoice"""
    invoice = frappe.get_doc({
        'doctype': 'Purchase Invoice', 
        'supplier': supplier,
        'due_date': frappe.utils.nowdate(),
        'items': [{
            'item_code': 'Test Item',
            'qty': 1,
            'rate': 500
        }]
    })
    invoice.insert()
    invoice.submit()
    return invoice.name

if __name__ == '__main__':
    unittest.main()