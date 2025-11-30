#!/usr/bin/env python3
"""
Script to create test data for development and testing
"""

import frappe
import random
from datetime import datetime, timedelta

def create_test_data():
    """
    Create comprehensive test data for payment system
    """
    try:
        print("Creating test data for Zambia Payments...")
        
        # Create test payment methods
        create_test_payment_methods()
        
        # Create test payment transactions
        create_test_payment_transactions()
        
        # Create test payment links
        create_test_payment_links()
        
        # Create test refunds
        create_test_refunds()
        
        print("Test data creation completed successfully!")
        
    except Exception as e:
        print(f"Test data creation failed: {str(e)}")
        frappe.log_error(f"Test data creation failed: {str(e)}", "Test Data Script")

def create_test_payment_methods():
    """Create test payment methods"""
    payment_methods = [
        {
            'payment_method': 'MTN Mobile Money',
            'enabled': 1,
            'processing_fee_percentage': 2.5,
            'fixed_fee': 2.0,
            'minimum_amount': 1.0,
            'maximum_amount': 5000.0,
            'icon': 'fa-mobile',
            'description': 'MTN Mobile Money payments for Zambia'
        },
        {
            'payment_method': 'Airtel Money',
            'enabled': 1,
            'processing_fee_percentage': 2.5,
            'fixed_fee': 2.0,
            'minimum_amount': 1.0,
            'maximum_amount': 5000.0,
            'icon': 'fa-mobile',
            'description': 'Airtel Money payments for Zambia'
        },
        {
            'payment_method': 'Visa Card',
            'enabled': 1,
            'processing_fee_percentage': 3.0,
            'fixed_fee': 2.5,
            'minimum_amount': 5.0,
            'maximum_amount': 10000.0,
            'icon': 'fa-credit-card',
            'description': 'Visa card payments'
        },
        {
            'payment_method': 'MasterCard',
            'enabled': 1,
            'processing_fee_percentage': 3.0,
            'fixed_fee': 2.5,
            'minimum_amount': 5.0,
            'maximum_amount': 10000.0,
            'icon': 'fa-credit-card',
            'description': 'MasterCard payments'
        }
    ]
    
    for method_data in payment_methods:
        if not frappe.db.exists('Payment Method', method_data['payment_method']):
            method = frappe.get_doc({
                'doctype': 'Payment Method',
                **method_data
            })
            method.insert()
            print(f"Created payment method: {method_data['payment_method']}")

def create_test_payment_transactions(count=20):
    """Create test payment transactions"""
    statuses = ['Completed', 'Pending', 'Failed', 'Refunded']
    payment_methods = ['MTN Mobile Money', 'Airtel Money', 'Visa Card', 'MasterCard']
    currencies = ['ZMW', 'USD']
    
    for i in range(count):
        status = random.choice(statuses)
        amount = round(random.uniform(10, 1000), 2)
        currency = random.choice(currencies)
        
        # Adjust amount for ZMW (typically whole numbers)
        if currency == 'ZMW':
            amount = round(amount)
        
        transaction_data = {
            'doctype': 'Payment Transaction',
            'reference_id': f'TEST_TXN_{datetime.now().strftime("%Y%m%d")}_{i:03d}',
            'amount': amount,
            'currency': currency,
            'status': status,
            'payment_method': random.choice(payment_methods),
            'customer_email': f'testcustomer{i}@example.com',
            'customer_phone': generate_test_phone_number(),
            'payment_initiated': generate_random_date(days_back=30)
        }
        
        if status == 'Completed':
            transaction_data['payment_completed'] = generate_random_date(days_back=15)
            transaction_data['transaction_id'] = f'GATEWAY_TXN_{random.randint(100000, 999999)}'
        
        if status == 'Failed':
            failure_reasons = [
                'Insufficient funds',
                'Card declined',
                'Network error',
                'Invalid phone number',
                'Transaction timeout'
            ]
            transaction_data['failure_reason'] = random.choice(failure_reasons)
        
        try:
            transaction = frappe.get_doc(transaction_data)
            transaction.insert(ignore_permissions=True)
            print(f"Created payment transaction: {transaction.reference_id}")
        except frappe.DuplicateEntryError:
            print(f"Transaction already exists: {transaction_data['reference_id']}")

def create_test_payment_links(count=10):
    """Create test payment links"""
    statuses = ['Pending', 'Paid', 'Cancelled', 'Expired']
    
    for i in range(count):
        amount = round(random.uniform(50, 500), 2)
        status = random.choice(statuses)
        
        link_data = {
            'doctype': 'Payment Link',
            'reference_id': f'TEST_PL_{datetime.now().strftime("%Y%m%d")}_{i:03d}',
            'linked_doctype': 'Sales Invoice',
            'linked_docname': f'ACC-SINV-2024-{i:05d}',
            'amount': amount,
            'currency': 'ZMW',
            'status': status,
            'customer_email': f'customer{i}@example.com',
            'customer_phone': generate_test_phone_number(),
            'expiry_date': datetime.now() + timedelta(days=random.randint(1, 30))
        }
        
        if status == 'Paid':
            # Find a completed transaction to link
            completed_txns = frappe.get_all('Payment Transaction',
                filters={'status': 'Completed'},
                fields=['name'],
                limit=1
            )
            if completed_txns:
                link_data['payment_transaction'] = completed_txns[0]['name']
        
        try:
            payment_link = frappe.get_doc(link_data)
            payment_link.insert(ignore_permissions=True)
            print(f"Created payment link: {payment_link.reference_id}")
        except frappe.DuplicateEntryError:
            print(f"Payment link already exists: {link_data['reference_id']}")

def create_test_refunds(count=5):
    """Create test refunds"""
    # Get completed transactions to refund
    completed_txns = frappe.get_all('Payment Transaction',
        filters={'status': 'Completed'},
        fields=['name', 'amount'],
        limit=count
    )
    
    for i, txn in enumerate(completed_txns):
        refund_amount = round(txn['amount'] * random.uniform(0.1, 1.0), 2)
        
        refund_data = {
            'doctype': 'Payment Refund',
            'payment_reference': txn['name'],
            'refund_amount': refund_amount,
            'original_amount': txn['amount'],
            'currency': 'ZMW',
            'reason': random.choice([
                'Customer request',
                'Service not provided',
                'Duplicate payment',
                'Technical error'
            ]),
            'status': random.choice(['Completed', 'Pending']),
            'customer_email': f'refund{i}@example.com'
        }
        
        try:
            refund = frappe.get_doc(refund_data)
            refund.insert(ignore_permissions=True)
            print(f"Created refund: {refund.name}")
        except Exception as e:
            print(f"Failed to create refund: {str(e)}")

def generate_test_phone_number():
    """Generate a test Zambian phone number"""
    prefixes = ['76', '77', '96', '97']
    prefix = random.choice(prefixes)
    number = ''.join([str(random.randint(0, 9)) for _ in range(7)])
    return f'+260{prefix}{number}'

def generate_random_date(days_back=30):
    """Generate a random date within the specified range"""
    random_days = random.randint(0, days_back)
    random_hours = random.randint(0, 23)
    random_minutes = random.randint(0, 59)
    
    return datetime.now() - timedelta(
        days=random_days,
        hours=random_hours,
        minutes=random_minutes
    )

@frappe.whitelist()
def cleanup_test_data():
    """Clean up test data"""
    try:
        # Delete test transactions
        test_transactions = frappe.get_all('Payment Transaction',
            filters={'reference_id': ['like', 'TEST_%']},
            fields=['name']
        )
        
        for txn in test_transactions:
            frappe.delete_doc('Payment Transaction', txn['name'])
        
        # Delete test payment links
        test_links = frappe.get_all('Payment Link',
            filters={'reference_id': ['like', 'TEST_%']},
            fields=['name']
        )
        
        for link in test_links:
            frappe.delete_doc('Payment Link', link['name'])
        
        # Delete test refunds
        test_refunds = frappe.get_all('Payment Refund',
            filters={'customer_email': ['like', 'refund%@example.com']},
            fields=['name']
        )
        
        for refund in test_refunds:
            frappe.delete_doc('Payment Refund', refund['name'])
        
        print("Test data cleanup completed")
        return {'success': True, 'deleted_count': len(test_transactions) + len(test_links) + len(test_refunds)}
    
    except Exception as e:
        print(f"Test data cleanup failed: {str(e)}")
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # For command line execution
    frappe.init(site='your-site-name')
    frappe.connect()
    
    try:
        create_test_data()
    finally:
        frappe.destroy()