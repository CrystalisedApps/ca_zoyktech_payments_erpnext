# webhooks.py
import frappe
import json
from frappe import _
from .zoyktech_client import ZoykTechClient
from .payment_integration import PaymentIntegration
from ..utils.security import validate_webhook_origin
from datetime import datetime

@frappe.whitelist(allow_guest=True, methods=['POST'])
def handle_zoyktech_callback():
    """
    Main webhook handler for ZoykTech payment callbacks
    This endpoint receives payment status updates from ZoykTech
    """
    try:
        # Get request data
        raw_payload = frappe.request.get_data(as_text=True)
        headers = dict(frappe.request.headers)
        
        # Log webhook receipt
        frappe.logger().info(f"ZoykTech Webhook Received: {headers.get('X-ZoykTech-Event-ID', 'Unknown')}")
        
        # Validate webhook signature
        signature = headers.get('X-ZoykTech-Signature')
        if not validate_webhook_signature(raw_payload, signature):
            frappe.log_error("Invalid webhook signature", "Webhook Security")
            return {"status": "error", "message": "Invalid signature"}, 401
        
        # Parse payload
        payload = json.loads(raw_payload)
        event_type = payload.get('event')
        event_data = payload.get('data', {})
        
        frappe.logger().info(f"Processing webhook event: {event_type}")
        
        # Process based on event type
        if event_type == 'payment.successful':
            return handle_successful_payment(event_data)
        elif event_type == 'payment.failed':
            return handle_failed_payment(event_data)
        elif event_type == 'payment.pending':
            return handle_pending_payment(event_data)
        elif event_type == 'payment.refunded':
            return handle_refunded_payment(event_data)
        elif event_type == 'payment.disputed':
            return handle_disputed_payment(event_data)
        else:
            frappe.log_error(f"Unknown webhook event: {event_type}", "Webhook Processing")
            return {"status": "error", "message": "Unknown event type"}, 400
            
    except json.JSONDecodeError as e:
        frappe.log_error(f"Invalid JSON in webhook: {str(e)}", "Webhook Error")
        return {"status": "error", "message": "Invalid JSON payload"}, 400
    except Exception as e:
        frappe.log_error(f"Webhook processing error: {str(e)}", "Webhook Error")
        return {"status": "error", "message": "Internal server error"}, 500

def validate_webhook_signature(payload: str, signature: str) -> bool:
    """Validate webhook signature using stored secret"""
    try:
        client = ZoykTechClient()
        return client.validate_webhook_signature(payload, signature)
    except Exception as e:
        frappe.log_error(f"Signature validation error: {str(e)}", "Webhook Security")
        return False

def handle_successful_payment(payment_data: dict):
    """Handle successful payment webhook"""
    try:
        reference = payment_data.get('reference')
        transaction_id = payment_data.get('transaction_id')
        
        if not reference:
            frappe.log_error("No reference in successful payment", "Webhook Processing")
            return {"status": "error", "message": "No reference provided"}, 400
        
        frappe.logger().info(f"Processing successful payment: {reference}")
        
        # Process payment using integration engine
        integration = PaymentIntegration()
        result = integration.process_successful_payment(reference, payment_data)
        
        if result.get('success'):
            # Log successful processing
            frappe.logger().info(f"Successfully processed payment: {reference}")
            
            # Send real-time update to clients
            frappe.publish_realtime('payment_completed', {
                'reference': reference,
                'transaction_id': transaction_id,
                'amount': payment_data.get('amount'),
                'currency': payment_data.get('currency'),
                'timestamp': datetime.now().isoformat()
            })
            
            return {
                "status": "success", 
                "message": "Payment processed successfully",
                "reference": reference
            }
        else:
            frappe.log_error(f"Failed to process payment: {result.get('error')}", "Payment Processing")
            return {"status": "error", "message": result.get('message')}, 500
            
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error handling successful payment: {str(e)}", "Payment Processing Error")
        return {"status": "error", "message": "Failed to process payment"}, 500

def handle_failed_payment(payment_data: dict):
    """Handle failed payment webhook"""
    try:
        reference = payment_data.get('reference')
        
        if not reference:
            return {"status": "error", "message": "No reference provided"}, 400
        
        frappe.logger().info(f"Processing failed payment: {reference}")
        
        # Update payment transaction
        update_payment_transaction_status(reference, "Failed", payment_data)
        
        # Update payment link
        update_payment_link_status(reference, "Failed")
        
        frappe.db.commit()
        
        # Notify relevant users
        notify_payment_failure(reference, payment_data)
        
        return {"status": "success", "message": "Payment failure recorded"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error handling failed payment: {str(e)}", "Payment Failure Error")
        return {"status": "error", "message": "Failed to record payment failure"}, 500

def handle_pending_payment(payment_data: dict):
    """Handle pending payment webhook"""
    try:
        reference = payment_data.get('reference')
        
        if not reference:
            return {"status": "error", "message": "No reference provided"}, 400
        
        # Update payment transaction
        update_payment_transaction_status(reference, "Pending", payment_data)
        
        frappe.db.commit()
        
        return {"status": "success", "message": "Payment pending status recorded"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error handling pending payment: {str(e)}", "Payment Pending Error")
        return {"status": "error", "message": "Failed to record pending payment"}, 500

def handle_refunded_payment(payment_data: dict):
    """Handle refunded payment webhook"""
    try:
        reference = payment_data.get('reference')
        refund_amount = payment_data.get('refund_amount')
        
        if not reference:
            return {"status": "error", "message": "No reference provided"}, 400
        
        frappe.logger().info(f"Processing refund for payment: {reference}")
        
        # Update payment transaction
        update_payment_transaction_status(reference, "Refunded", payment_data)
        
        # Create refund record
        create_refund_record(reference, refund_amount, payment_data)
        
        frappe.db.commit()
        
        return {"status": "success", "message": "Payment refund recorded"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error handling refunded payment: {str(e)}", "Payment Refund Error")
        return {"status": "error", "message": "Failed to record payment refund"}, 500

def handle_disputed_payment(payment_data: dict):
    """Handle disputed payment webhook"""
    try:
        reference = payment_data.get('reference')
        
        if not reference:
            return {"status": "error", "message": "No reference provided"}, 400
        
        frappe.logger().warning(f"Processing disputed payment: {reference}")
        
        # Update payment transaction
        update_payment_transaction_status(reference, "Disputed", payment_data)
        
        # Create dispute record
        create_dispute_record(reference, payment_data)
        
        frappe.db.commit()
        
        return {"status": "success", "message": "Payment dispute recorded"}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error handling disputed payment: {str(e)}", "Payment Dispute Error")
        return {"status": "error", "message": "Failed to record payment dispute"}, 500

def update_payment_transaction_status(reference: str, status: str, payment_data: dict):
    """Update payment transaction status"""
    try:
        payment_txn = frappe.get_doc("Payment Transaction", reference)
        payment_txn.status = status
        payment_txn.gateway_response = json.dumps(payment_data, indent=2)
        
        if status == "Failed":
            payment_txn.failure_reason = payment_data.get('failure_reason', 'Unknown error')
        
        payment_txn.save(ignore_permissions=True)
        
    except frappe.DoesNotExistError:
        # Create new transaction if it doesn't exist
        payment_txn = frappe.new_doc("Payment Transaction")
        payment_txn.reference_id = reference
        payment_txn.amount = payment_data.get('amount', 0)
        payment_txn.currency = payment_data.get('currency', 'ZMW')
        payment_txn.status = status
        payment_txn.customer_email = payment_data.get('customer_email')
        payment_txn.customer_phone = payment_data.get('customer_phone')
        payment_txn.gateway_response = json.dumps(payment_data, indent=2)
        payment_txn.payment_initiated = datetime.now()
        
        if status == "Completed":
            payment_txn.payment_completed = datetime.now()
        
        payment_txn.insert(ignore_permissions=True)

def update_payment_link_status(reference: str, status: str):
    """Update payment link status"""
    payment_links = frappe.get_all("Payment Link",
        filters={"reference_id": reference},
        fields=["name"])
    
    for link in payment_links:
        payment_link = frappe.get_doc("Payment Link", link.name)
        payment_link.status = status
        payment_link.save(ignore_permissions=True)

def notify_payment_failure(reference: str, payment_data: dict):
    """Notify relevant users about payment failure"""
    try:
        # Get payment link details
        payment_links = frappe.get_all("Payment Link",
            filters={"reference_id": reference},
            fields=["linked_doctype", "linked_docname", "customer_email"])
        
        for link in payment_links:
            # Send email notification
            if link.customer_email:
                send_payment_failure_email(link.customer_email, reference, payment_data)
            
            # Create system notification
            frappe.publish_realtime('payment_failed', {
                'reference': reference,
                'doctype': link.linked_doctype,
                'docname': link.linked_docname,
                'reason': payment_data.get('failure_reason', 'Unknown error')
            })
            
    except Exception as e:
        frappe.log_error(f"Error sending failure notification: {str(e)}", "Notification Error")

def send_payment_failure_email(email: str, reference: str, payment_data: dict):
    """Send payment failure email"""
    try:
        subject = _("Payment Failed - Reference: {0}").format(reference)
        message = _("""
        Dear Customer,

        Your payment with reference {reference} has failed.

        Failure Reason: {reason}
        Amount: {amount} {currency}

        Please try again or contact support if the issue persists.

        Best regards,
        Payment Team
        """).format(
            reference=reference,
            reason=payment_data.get('failure_reason', 'Unknown error'),
            amount=payment_data.get('amount', 0),
            currency=payment_data.get('currency', 'ZMW')
        )
        
        frappe.sendmail(
            recipients=email,
            subject=subject,
            message=message
        )
        
    except Exception as e:
        frappe.log_error(f"Error sending failure email: {str(e)}", "Email Error")

def create_refund_record(reference: str, refund_amount: float, payment_data: dict):
    """Create refund record for accounting purposes"""
    try:
        refund = frappe.new_doc("Payment Refund")
        refund.payment_reference = reference
        refund.refund_amount = refund_amount
        refund.original_amount = payment_data.get('amount', 0)
        refund.currency = payment_data.get('currency', 'ZMW')
        refund.reason = payment_data.get('refund_reason', 'Customer request')
        refund.transaction_id = payment_data.get('refund_transaction_id')
        refund.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error creating refund record: {str(e)}", "Refund Record Error")

def create_dispute_record(reference: str, payment_data: dict):
    """Create dispute record for tracking"""
    try:
        dispute = frappe.new_doc("Payment Dispute")
        dispute.payment_reference = reference
        dispute.dispute_reason = payment_data.get('dispute_reason', 'Unknown')
        dispute.dispute_amount = payment_data.get('dispute_amount', 0)
        dispute.status = "Open"
        dispute.insert(ignore_permissions=True)
        
    except Exception as e:
        frappe.log_error(f"Error creating dispute record: {str(e)}", "Dispute Record Error")

@frappe.whitelist()
def get_webhook_logs(days: int = 7):
    """Get recent webhook logs for debugging"""
    from datetime import datetime, timedelta
    
    since_date = datetime.now() - timedelta(days=days)
    
    logs = frappe.get_all("Error Log",
        filters={
            "creation": [">=", since_date],
            "method": ["like", "%webhook%"]
        },
        fields=["name", "method", "error", "creation"],
        order_by="creation desc",
        limit=50
    )
    
    return logs