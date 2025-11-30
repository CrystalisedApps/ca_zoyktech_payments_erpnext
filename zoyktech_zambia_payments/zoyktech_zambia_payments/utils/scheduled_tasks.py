import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, add_days
from datetime import datetime, timedelta
import json

def reconcile_pending_payments():
    """
    Reconcile pending payments that are older than 24 hours
    This runs daily via scheduler
    """
    try:
        # Get payments pending for more than 24 hours
        cutoff_time = now_datetime() - timedelta(hours=24)
        
        pending_payments = frappe.get_all("Payment Transaction",
            filters={
                "status": "Pending",
                "payment_initiated": ["<", cutoff_time]
            },
            fields=["name", "reference_id", "amount", "customer_email"]
        )
        
        for payment in pending_payments:
            try:
                # Update status to expired
                frappe.db.set_value("Payment Transaction", payment.name, "status", "Expired")
                
                # Also update payment link if exists
                payment_links = frappe.get_all("Payment Link",
                    filters={"reference_id": payment.reference_id},
                    fields=["name"]
                )
                
                for link in payment_links:
                    frappe.db.set_value("Payment Link", link.name, "status", "Expired")
                
                frappe.logger().info(f"Expired pending payment: {payment.reference_id}")
                
            except Exception as e:
                frappe.log_error(f"Error expiring payment {payment.reference_id}: {str(e)}", "Payment Reconciliation")
        
        frappe.db.commit()
        frappe.logger().info(f"Reconciled {len(pending_payments)} pending payments")
        
    except Exception as e:
        frappe.log_error(f"Error in reconcile_pending_payments: {str(e)}", "Scheduled Task Error")

def check_pending_payments():
    """
    Check pending payments and update their status from gateway
    This runs hourly
    """
    try:
        from zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration import PaymentIntegration
        
        # Get payments pending for more than 1 hour but less than 24 hours
        one_hour_ago = now_datetime() - timedelta(hours=1)
        twenty_four_hours_ago = now_datetime() - timedelta(hours=24)
        
        pending_payments = frappe.get_all("Payment Transaction",
            filters={
                "status": "Pending",
                "payment_initiated": [">=", twenty_four_hours_ago],
                "payment_initiated": ["<=", one_hour_ago]
            },
            fields=["name", "reference_id"]
        )
        
        integration = PaymentIntegration()
        
        for payment in pending_payments:
            try:
                # Check payment status from gateway
                status_result = integration.get_payment_status(payment.reference_id)
                
                if status_result.get("success") and status_result.get("status") != "Pending":
                    # Status changed, process accordingly
                    if status_result.get("status") == "Completed":
                        # This should ideally come via webhook, but we can process it here too
                        frappe.logger().info(f"Payment {payment.reference_id} completed via status check")
                    elif status_result.get("status") == "Failed":
                        frappe.db.set_value("Payment Transaction", payment.name, "status", "Failed")
                
            except Exception as e:
                frappe.log_error(f"Error checking payment status {payment.reference_id}: {str(e)}", "Payment Status Check")
        
        frappe.logger().info(f"Checked status for {len(pending_payments)} pending payments")
        
    except Exception as e:
        frappe.log_error(f"Error in check_pending_payments: {str(e)}", "Scheduled Task Error")

def send_payment_reports():
    """
    Send daily payment reports to administrators
    This runs daily
    """
    try:
        # Get yesterday's date
        yesterday = getdate() - timedelta(days=1)
        
        # Get successful payments from yesterday
        successful_payments = frappe.get_all("Payment Transaction",
            filters={
                "status": "Completed",
                "payment_completed": [">=", yesterday],
                "payment_completed": ["<", getdate()]
            },
            fields=["COUNT(*) as count", "SUM(amount) as total"]
        )[0]
        
        # Get failed payments from yesterday
        failed_payments = frappe.get_all("Payment Transaction",
            filters={
                "status": "Failed", 
                "payment_initiated": [">=", yesterday],
                "payment_initiated": ["<", getdate()]
            },
            fields=["COUNT(*) as count"]
        )[0]
        
        # Prepare report data
        report_data = {
            "date": yesterday.strftime("%Y-%m-%d"),
            "successful_count": successful_payments.count or 0,
            "successful_total": successful_payments.total or 0,
            "failed_count": failed_payments.count or 0
        }
        
        # Get admin emails
        admin_emails = frappe.get_all("User",
            filters={"enabled": 1, "role_profile_name": "System Manager"},
            fields=["email"]
        )
        
        if admin_emails and (report_data["successful_count"] > 0 or report_data["failed_count"] > 0):
            recipients = [admin["email"] for admin in admin_emails]
            
            subject = _("Daily Payment Report - {0}").format(yesterday.strftime("%Y-%m-%d"))
            
            message = _("""
            Daily Payment Report for {date}
            
            Summary:
            - Successful Payments: {successful_count}
            - Total Amount Collected: ZMW {successful_total:,.2f}
            - Failed Payments: {failed_count}
            
            Best regards,
            Payment System
            """).format(**report_data)
            
            frappe.sendmail(
                recipients=recipients,
                subject=subject,
                message=message
            )
            
            frappe.logger().info(f"Sent daily payment report to {len(recipients)} admins")
        
    except Exception as e:
        frappe.log_error(f"Error in send_payment_reports: {str(e)}", "Scheduled Task Error")

def cleanup_old_payments():
    """
    Clean up old payment records (older than 90 days)
    This can be run monthly
    """
    try:
        cutoff_date = now_datetime() - timedelta(days=90)
        
        # Get old payment transactions
        old_payments = frappe.get_all("Payment Transaction",
            filters={
                "payment_initiated": ["<", cutoff_date],
                "status": ["in", ["Completed", "Failed", "Cancelled"]]
            },
            fields=["name"]
        )
        
        for payment in old_payments:
            try:
                # Archive or delete old payments
                # For now, we'll just log them - in production you might want to archive
                frappe.logger().info(f"Would archive old payment: {payment.name}")
                
            except Exception as e:
                frappe.log_error(f"Error cleaning up payment {payment.name}: {str(e)}", "Payment Cleanup")
        
        frappe.logger().info(f"Identified {len(old_payments)} old payments for cleanup")
        
    except Exception as e:
        frappe.log_error(f"Error in cleanup_old_payments: {str(e)}", "Scheduled Task Error")