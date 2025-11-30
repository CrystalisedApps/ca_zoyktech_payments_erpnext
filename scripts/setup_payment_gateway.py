import frappe
from frappe import _
from frappe.installer import add_to_installed_apps

def setup_payment_gateway():
    """Setup payment gateway after installation"""
    
    # Create Payment Gateway Settings
    if not frappe.db.exists('DocType', 'Payment Gateway Settings'):
        create_payment_gateway_settings()
    
    # Create default payment methods
    create_default_payment_methods()
    
    # Create custom fields
    create_custom_fields()
    
    # Create mode of payments
    create_mode_of_payments()
    
    frappe.db.commit()
    
    print("Zambia Payments app setup completed successfully!")

def create_payment_gateway_settings():
    """Create payment gateway settings"""
    if not frappe.db.exists('Payment Gateway Settings', 'Payment Gateway Settings'):
        settings = frappe.get_doc({
            'doctype': 'Payment Gateway Settings',
            'gateway_name': 'ZoykTech',
            'is_test_mode': 1,
            'zoyktech_base_url': 'https://api.zoyktech.com',
            'test_base_url': 'https://sandbox.zoyktech.com'
        })
        settings.insert()

def create_default_payment_methods():
    """Create default payment methods"""
    default_methods = [
        {
            'payment_method': 'MTN Mobile Money',
            'enabled': 1,
            'processing_fee_percentage': 2.5,
            'fixed_fee': 2.0,
            'icon': 'fa-mobile',
            'description': 'MTN Mobile Money payments'
        },
        {
            'payment_method': 'Airtel Money', 
            'enabled': 1,
            'processing_fee_percentage': 2.5,
            'fixed_fee': 2.0,
            'icon': 'fa-mobile',
            'description': 'Airtel Money payments'
        },
        {
            'payment_method': 'Visa Card',
            'enabled': 1, 
            'processing_fee_percentage': 3.0,
            'fixed_fee': 2.5,
            'icon': 'fa-credit-card',
            'description': 'Visa card payments'
        },
        {
            'payment_method': 'MasterCard',
            'enabled': 1,
            'processing_fee_percentage': 3.0, 
            'fixed_fee': 2.5,
            'icon': 'fa-credit-card',
            'description': 'MasterCard payments'
        },
        {
            'payment_method': 'Bank Transfer',
            'enabled': 1,
            'processing_fee_percentage': 1.0,
            'fixed_fee': 5.0,
            'icon': 'fa-university',
            'description': 'Bank transfer payments'
        }
    ]
    
    for method_data in default_methods:
        if not frappe.db.exists('Payment Method', method_data['payment_method']):
            method = frappe.get_doc({
                'doctype': 'Payment Method',
                **method_data
            })
            method.insert()

def create_custom_fields():
    """Create custom fields for ERPNext integration"""
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    
    custom_fields = {
        'Sales Invoice': [
            {
                'fieldname': 'custom_payment_link_section',
                'fieldtype': 'Section Break',
                'insert_after': 'payment_terms_section',
                'label': 'Payment Links'
            },
            {
                'fieldname': 'custom_payment_links', 
                'fieldtype': 'HTML',
                'insert_after': 'custom_payment_link_section',
                'label': 'Payment Links'
            }
        ],
        'Payment Entry': [
            {
                'fieldname': 'custom_gateway_reference',
                'fieldtype': 'Data', 
                'insert_after': 'reference_no',
                'label': 'Gateway Reference',
                'read_only': 1
            }
        ],
        'Customer': [
            {
                'fieldname': 'custom_payment_history_section',
                'fieldtype': 'Section Break',
                'insert_after': 'payment_terms', 
                'label': 'Payment History'
            },
            {
                'fieldname': 'custom_payment_history',
                'fieldtype': 'HTML',
                'insert_after': 'custom_payment_history_section',
                'label': 'Payment History'
            }
        ]
    }
    
    create_custom_fields(custom_fields)

def create_mode_of_payments():
    """Create mode of payments for payment entries"""
    modes = ['Mobile Money', 'Card Payment', 'Bank Transfer']
    
    for mode in modes:
        if not frappe.db.exists('Mode of Payment', mode):
            mode_doc = frappe.get_doc({
                'doctype': 'Mode of Payment',
                'mode_of_payment': mode,
                'type': 'Phone' if 'Mobile' in mode else 'Card' if 'Card' in mode else 'Bank'
            })
            mode_doc.insert()

def after_install():
    """Run after app installation"""
    try:
        setup_payment_gateway()
        print("Zambia Payments app installed successfully!")
    except Exception as e:
        print(f"Error during installation: {str(e)}")
        frappe.db.rollback()

if __name__ == '__main__':
    setup_payment_gateway()