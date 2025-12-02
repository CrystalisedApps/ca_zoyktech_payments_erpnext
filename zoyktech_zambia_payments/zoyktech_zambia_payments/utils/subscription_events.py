# subscription_events.py

import frappe
from frappe import _
from .subscription_payment_handler import SubscriptionPaymentHandler

def on_subscription_submit(doc, method=None):
    """
    Triggered when subscription is submitted
    Create immediate payment if subscription is active
    """
    try:
        if doc.docstatus == 1 and doc.status == "Active":
            handler = SubscriptionPaymentHandler()
            result = handler.create_immediate_subscription_payment(doc.name)
            
            if result and not result.get("success"):
                frappe.msgprint(_("Payment creation failed: {0}").format(result.get("message")), alert=True)
            elif result and result.get("success"):
                frappe.msgprint(_("Payment initiated successfully. Reference: {0}").format(
                    result.get("reference_id")), alert=True)
                
    except Exception as e:
        frappe.log_error(f"Error in subscription submit handler: {str(e)}", "Subscription Submit Error")
        frappe.msgprint(_("Error creating payment: {0}").format(str(e)), alert=True)

def on_subscription_update(doc, method=None):
    """
    Handle subscription status changes
    Create payment when subscription becomes active
    """
    try:
        if doc.has_value_changed("status"):
            old_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
            
            if old_status != "Active" and doc.status == "Active":
                handler = SubscriptionPaymentHandler()
                result = handler.create_immediate_subscription_payment(doc.name)
                
                if result and result.get("success"):
                    frappe.msgprint(_("Payment initiated for activated subscription"), alert=True)
                    
    except Exception as e:
        frappe.log_error(f"Error in subscription update handler: {str(e)}", "Subscription Update Error")