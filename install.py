# install.py

import frappe
from frappe import _

def after_install():
    """Run after app installation"""
    create_custom_fields()

def create_custom_fields():
    """Create custom fields programmatically"""
    custom_fields = [
        # Sales Invoice fields
        {
            "dt": "Sales Invoice",
            "fieldname": "custom_subscription_id",
            "fieldtype": "Link",
            "options": "Subscription",
            "label": "Subscription ID",
            "insert_after": "contact_mobile",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "custom_payment_reference",
            "fieldtype": "Data",
            "label": "Payment Reference",
            "insert_after": "custom_subscription_id",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Sales Invoice",
            "fieldname": "custom_payment_method",
            "fieldtype": "Data",
            "label": "Payment Method",
            "insert_after": "custom_payment_reference",
            "read_only": 1,
            "no_copy": 1
        },
        
        # Subscription fields
        {
            "dt": "Subscription",
            "fieldname": "custom_payment_reference",
            "fieldtype": "Data",
            "label": "Payment Reference",
            "insert_after": "status",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Subscription",
            "fieldname": "custom_payment_status",
            "fieldtype": "Select",
            "options": "\nPending\nPaid\nFailed\nTimed Out",
            "label": "Payment Status",
            "insert_after": "custom_payment_reference",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Subscription",
            "fieldname": "custom_payment_transaction",
            "fieldtype": "Link",
            "options": "Payment Transaction",
            "label": "Payment Transaction",
            "insert_after": "custom_payment_status",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Subscription",
            "fieldname": "custom_last_payment_date",
            "fieldtype": "Date",
            "label": "Last Payment Date",
            "insert_after": "current_invoice_end",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Subscription",
            "fieldname": "custom_last_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "label": "Last Invoice",
            "insert_after": "custom_last_payment_date",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Subscription",
            "fieldname": "custom_last_payment",
            "fieldtype": "Link",
            "options": "Payment Entry",
            "label": "Last Payment",
            "insert_after": "custom_last_invoice",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Subscription",
            "fieldname": "custom_payment_link",
            "fieldtype": "Link",
            "options": "Payment Link",
            "label": "Payment Link",
            "insert_after": "custom_last_payment",
            "read_only": 1,
            "no_copy": 1
        },
        
        # Payment Entry fields (will be created only if Payment Entry doctype exists)
        {
            "dt": "Payment Entry",
            "fieldname": "custom_is_subscription_payment",
            "fieldtype": "Check",
            "label": "Is Subscription Payment",
            "insert_after": "reference_no",
            "read_only": 1,
            "no_copy": 1
        },
        {
            "dt": "Payment Entry",
            "fieldname": "custom_subscription_id",
            "fieldtype": "Link",
            "options": "Subscription",
            "label": "Subscription ID",
            "insert_after": "custom_is_subscription_payment",
            "read_only": 1,
            "no_copy": 1
        }
    ]
    
    for field_data in custom_fields:
        try:
            # Check if doctype exists before creating custom field
            if frappe.db.exists("DocType", field_data["dt"]):
                if not frappe.db.exists("Custom Field", {
                    "dt": field_data["dt"],
                    "fieldname": field_data["fieldname"]
                }):
                    custom_field = frappe.get_doc({
                        "doctype": "Custom Field",
                        "dt": field_data["dt"],
                        "module": "Zoyktech Zambia Payments",
                        **field_data
                    })
                    custom_field.insert(ignore_permissions=True)
                    frappe.db.commit()
        except Exception as e:
            frappe.log_error(f"Error creating custom field {field_data['fieldname']}: {str(e)}", "Custom Field Creation")