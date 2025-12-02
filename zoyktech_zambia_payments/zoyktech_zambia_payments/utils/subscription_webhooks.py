# subscription_webhooks.py

import frappe
import json
from frappe import _
from .subscription_payment_handler import SubscriptionPaymentHandler

@frappe.whitelist(allow_guest=True, methods=['POST'])
def handle_subscription_payment_callback():
    """
    Webhook endpoint for subscription payment callbacks
    """
    try:
        # Get request data
        raw_payload = frappe.request.get_data(as_text=True)
        payload = json.loads(raw_payload)
        
        event_type = payload.get('event')
        event_data = payload.get('data', {})
        reference_id = event_data.get('reference')
        
        if not reference_id:
            return {"status": "error", "message": "No reference ID provided"}, 400
        
        frappe.logger().info(f"Subscription webhook received: {event_type} for {reference_id}")
        
        # Initialize handler
        handler = SubscriptionPaymentHandler()
        
        # Process based on event type
        if event_type == 'payment.successful':
            # Update payment in ERPNext
            result = handler.handle_subscription_webhook(reference_id, event_data)
            
            if result.get("success"):
                return {
                    "status": "success",
                    "message": "Subscription payment processed successfully"
                }
            else:
                return {
                    "status": "error",
                    "message": result.get("message", "Unknown error")
                }, 500
                
        elif event_type == 'payment.failed':
            # Handle failed payment
            # Find subscription from payment transaction
            try:
                payment_txn = frappe.get_doc("Payment Transaction", reference_id)
                payment_link = frappe.get_doc("Payment Link", {"payment_transaction": payment_txn.name})
                
                if payment_link:
                    subscription = frappe.get_doc("Subscription", payment_link.linked_docname)
                    subscription.custom_payment_status = "Failed"
                    subscription.save(ignore_permissions=True)
            except:
                pass
            
            return {"status": "success", "message": "Payment failure recorded"}
        
        else:
            frappe.logger().info(f"Unhandled webhook event: {event_type}")
            return {"status": "success", "message": "Event received but not processed"}
            
    except json.JSONDecodeError as e:
        frappe.log_error(f"Invalid JSON in webhook: {str(e)}", "Subscription Webhook Error")
        return {"status": "error", "message": "Invalid JSON payload"}, 400
    except Exception as e:
        frappe.log_error(f"Subscription webhook processing error: {str(e)}", "Subscription Webhook Error")
        return {"status": "error", "message": "Internal server error"}, 500