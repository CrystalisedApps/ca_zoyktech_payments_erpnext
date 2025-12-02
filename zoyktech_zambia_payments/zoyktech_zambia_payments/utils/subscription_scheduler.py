# subscription_scheduler.py

import frappe
from frappe.utils import nowdate

def process_due_subscriptions():
    """
    Process due subscriptions for recurring payments
    Runs daily to check for subscriptions that need renewal
    """
    try:
        # Get active subscriptions with due payments
        due_subscriptions = frappe.get_all("Subscription",
            filters={
                "status": "Active",
                "recurring": 1,
                "current_invoice_end": ["<", nowdate()]
            },
            fields=["name", "customer", "subscription_plan", "total", "currency"]
        )
        
        # Import handler here to avoid circular imports
        from .subscription_payment_handler import SubscriptionPaymentHandler
        handler = SubscriptionPaymentHandler()
        
        for subscription in due_subscriptions:
            try:
                frappe.logger().info(f"Processing due subscription: {subscription.name}")
                
                # Create payment for due subscription
                result = handler.create_immediate_subscription_payment(subscription.name)
                
                if result.get("success"):
                    frappe.logger().info(f"Successfully created payment for subscription {subscription.name}")
                else:
                    frappe.logger().error(f"Failed to create payment for subscription {subscription.name}: {result.get('message')}")
                    
            except Exception as e:
                frappe.log_error(f"Error processing subscription {subscription.name}: {str(e)}", "Subscription Processing Error")
                continue
                
    except Exception as e:
        frappe.log_error(f"Error in process_due_subscriptions: {str(e)}", "Subscription Scheduler Error")

def check_pending_subscription_payments():
    """
    Check for pending subscription payments that need status updates
    Runs hourly
    """
    try:
        # Get subscriptions with pending payments
        pending_subscriptions = frappe.get_all("Subscription",
            filters={
                "custom_payment_status": "Pending",
                "custom_payment_reference": ["!=", ""]
            },
            fields=["name", "custom_payment_reference"]
        )
        
        from ..api.payment_integration import PaymentIntegration
        integration = PaymentIntegration()
        
        for subscription in pending_subscriptions:
            try:
                # Check payment status
                status_response = integration.get_payment_status(subscription.custom_payment_reference)
                
                if status_response.get("success"):
                    status = status_response.get("status")
                    
                    if status == "Completed":
                        # Payment completed - update subscription
                        sub_doc = frappe.get_doc("Subscription", subscription.name)
                        sub_doc.custom_payment_status = "Paid"
                        sub_doc.save(ignore_permissions=True)
                        
                    elif status == "Failed":
                        # Payment failed
                        sub_doc = frappe.get_doc("Subscription", subscription.name)
                        sub_doc.custom_payment_status = "Failed"
                        sub_doc.save(ignore_permissions=True)
                        
            except Exception as e:
                frappe.log_error(f"Error checking payment status for subscription {subscription.name}: {str(e)}", "Payment Status Check")
                continue
                
    except Exception as e:
        frappe.log_error(f"Error in check_pending_subscription_payments: {str(e)}", "Subscription Scheduler Error")