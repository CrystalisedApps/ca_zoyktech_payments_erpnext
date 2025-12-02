# subscription_payment_handler.py

import frappe
from frappe import _
from datetime import datetime, timedelta
import json
from ..api.payment_integration import PaymentIntegration
from ..api.zoyktech_client import ZoykTechClient

class SubscriptionPaymentHandler:
    """Handle automated payments for ERPNext Subscriptions"""
    
    def __init__(self):
        self.payment_integration = PaymentIntegration()
    
    def create_immediate_subscription_payment(self, subscription_name):
        """
        Create immediate payment when subscription is created/activated
        """
        try:
            # Get subscription document
            subscription = frappe.get_doc("Subscription", subscription_name)
            
            # Validate subscription
            if not self.validate_subscription_for_payment(subscription):
                return {
                    "success": False,
                    "message": _("Subscription not ready for payment")
                }
            
            # Step 1: Create Payment Link
            payment_link_response = self.create_subscription_payment_link(subscription)
            
            if not payment_link_response.get("success"):
                return payment_link_response
            
            # Step 2: Create Payment Transaction
            payment_txn_response = self.create_subscription_payment_transaction(
                subscription, 
                payment_link_response.get("payment_link_name")
            )
            
            if not payment_txn_response.get("success"):
                return payment_txn_response
            
            # Step 3: Start payment monitoring
            frappe.enqueue(
                self.monitor_subscription_payment,
                subscription_name=subscription_name,
                payment_link_name=payment_link_response.get("payment_link_name"),
                reference_id=payment_txn_response.get("reference_id"),
                queue='long',
                job_name=f"monitor_sub_payment_{subscription_name}"
            )
            
            return {
                "success": True,
                "message": _("Subscription payment process initiated"),
                "payment_link": payment_link_response.get("payment_link_name"),
                "payment_transaction": payment_txn_response.get("payment_transaction_name"),
                "reference_id": payment_txn_response.get("reference_id")
            }
            
        except Exception as e:
            frappe.log_error(f"Error creating subscription payment: {str(e)}", "Subscription Payment Error")
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to initiate subscription payment")
            }
    
    def validate_subscription_for_payment(self, subscription):
        """Validate if subscription is ready for payment"""
        if subscription.docstatus != 1:
            frappe.throw(_("Subscription must be submitted before payment"))
        
        if subscription.status not in ["Active", "Pending"]:
            frappe.throw(_("Subscription must be Active or Pending for payment"))
        
        if subscription.total <= 0:
            frappe.throw(_("Subscription amount must be greater than 0"))
        
        if not subscription.customer:
            frappe.throw(_("Customer is required for subscription payment"))
        
        return True
    
    def create_subscription_payment_link(self, subscription):
        """Create Payment Link for subscription"""
        try:
            # Get customer details
            customer = frappe.get_doc("Customer", subscription.customer)
            
            # Generate unique reference
            reference_id = f"SUB_{subscription.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create Payment Link document
            payment_link = frappe.new_doc("Payment Link")
            payment_link.reference_id = reference_id
            payment_link.linked_doctype = "Subscription"
            payment_link.linked_docname = subscription.name
            payment_link.amount = subscription.total
            payment_link.currency = subscription.currency or "ZMW"
            payment_link.status = "Pending"
            payment_link.payment_method = subscription.payment_method or "MTN Mobile Money"
            
            # Set expiry date (default 24 hours)
            payment_link.expiry_date = datetime.now() + timedelta(hours=24)
            
            # Add customer details
            payment_link.customer_name = customer.customer_name
            payment_link.customer_email = customer.email_id
            payment_link.customer_phone = customer.mobile_no or customer.phone
            
            # Add subscription metadata
            payment_link.description = f"Subscription Payment: {subscription.subscription_plan}"
            
            payment_link.insert(ignore_permissions=True)
            
            return {
                "success": True,
                "payment_link_name": payment_link.name,
                "reference_id": reference_id
            }
            
        except Exception as e:
            frappe.log_error(f"Error creating payment link: {str(e)}", "Payment Link Creation Error")
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to create payment link")
            }
    
    def create_subscription_payment_transaction(self, subscription, payment_link_name):
        """Create Payment Transaction for subscription"""
        try:
            customer = frappe.get_doc("Customer", subscription.customer)
            
            # Generate transaction reference
            reference_id = f"TXN_SUB_{subscription.name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create Payment Transaction
            payment_txn = frappe.new_doc("Payment Transaction")
            payment_txn.reference_id = reference_id
            payment_txn.amount = subscription.total
            payment_txn.currency = subscription.currency or "ZMW"
            payment_txn.status = "Pending"
            payment_txn.payment_method = subscription.payment_method or "MTN Mobile Money"
            payment_txn.customer_email = customer.email_id
            payment_txn.customer_phone = customer.mobile_no or customer.phone
            payment_txn.payment_initiated = datetime.now()
            
            # Set metadata
            metadata = {
                "doctype": "Subscription",
                "docname": subscription.name,
                "customer": subscription.customer,
                "plan": subscription.subscription_plan,
                "payment_link": payment_link_name,
                "frequency": subscription.billing_interval or "Monthly"
            }
            payment_txn.gateway_response = json.dumps(metadata, indent=2)
            
            payment_txn.insert(ignore_permissions=True)
            
            # Update Payment Link with transaction reference
            payment_link = frappe.get_doc("Payment Link", payment_link_name)
            payment_link.payment_transaction = payment_txn.name
            payment_link.save(ignore_permissions=True)
            
            return {
                "success": True,
                "payment_transaction_name": payment_txn.name,
                "reference_id": reference_id
            }
            
        except Exception as e:
            frappe.log_error(f"Error creating payment transaction: {str(e)}", "Payment Transaction Error")
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to create payment transaction")
            }
    
    def monitor_subscription_payment(self, subscription_name, payment_link_name, reference_id, max_attempts=60, interval=30):
        """
        Monitor subscription payment status
        """
        attempts = 0
        
        while attempts < max_attempts:
            try:
                # Get current status
                payment_link = frappe.get_doc("Payment Link", payment_link_name)
                payment_txn = frappe.get_doc("Payment Transaction", reference_id)
                
                # Check if payment is completed
                if payment_link.status == "Paid" and payment_txn.status == "Completed":
                    # Payment successful - process subscription
                    self.process_successful_subscription_payment(
                        subscription_name, 
                        payment_link_name, 
                        payment_txn.name
                    )
                    return True
                
                # Check if payment failed
                elif payment_link.status == "Failed" or payment_txn.status == "Failed":
                    self.handle_failed_subscription_payment(subscription_name, payment_link_name)
                    return False
                
                # Still pending, check with payment gateway
                status_response = self.payment_integration.get_payment_status(reference_id)
                if status_response.get("success") and status_response.get("status") == "Completed":
                    # Update documents
                    self.update_payment_documents_success(payment_link_name, payment_txn.name, status_response)
                    
                    # Process successful payment
                    self.process_successful_subscription_payment(
                        subscription_name, 
                        payment_link_name, 
                        payment_txn.name
                    )
                    return True
                
                attempts += 1
                frappe.sleep(interval)
                
            except Exception as e:
                frappe.log_error(f"Error monitoring payment: {str(e)}", "Payment Monitoring Error")
                attempts += 1
                frappe.sleep(interval)
        
        # Payment timeout
        self.handle_payment_timeout(subscription_name, payment_link_name, reference_id)
        return False
    
    def update_payment_documents_success(self, payment_link_name, payment_txn_name, gateway_response):
        """Update payment documents with successful payment"""
        try:
            # Update Payment Link
            payment_link = frappe.get_doc("Payment Link", payment_link_name)
            payment_link.status = "Paid"
            payment_link.save(ignore_permissions=True)
            
            # Update Payment Transaction
            payment_txn = frappe.get_doc("Payment Transaction", payment_txn_name)
            payment_txn.status = "Completed"
            payment_txn.transaction_id = gateway_response.get("transaction_id")
            payment_txn.payment_completed = datetime.now()
            payment_txn.save(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error updating payment documents: {str(e)}", "Payment Document Update Error")
    
    def process_successful_subscription_payment(self, subscription_name, payment_link_name, payment_txn_name):
        """
        Process successful subscription payment
        1. Create Sales Invoice
        2. Create Payment Entry for invoice
        3. Update subscription status
        """
        try:
            frappe.db.begin()
            
            # Get documents
            subscription = frappe.get_doc("Subscription", subscription_name)
            payment_link = frappe.get_doc("Payment Link", payment_link_name)
            payment_txn = frappe.get_doc("Payment Transaction", payment_txn_name)
            
            # Step 1: Create Sales Invoice
            sales_invoice = self.create_subscription_sales_invoice(subscription, payment_txn)
            
            # Step 2: Create Payment Entry for the invoice
            payment_entry = self.create_payment_for_invoice(sales_invoice.name, payment_txn)
            
            # Step 3: Update subscription with payment info
            self.update_subscription_after_payment(subscription, sales_invoice, payment_entry, payment_link)
            
            frappe.db.commit()
            
            # Send notification
            self.send_subscription_activated_notification(subscription, sales_invoice)
            
            frappe.logger().info(f"Subscription payment processed successfully for {subscription_name}")
            
            return {
                "success": True,
                "sales_invoice": sales_invoice.name,
                "payment_entry": payment_entry.name,
                "message": _("Subscription activated successfully")
            }
            
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error processing successful subscription payment: {str(e)}", "Subscription Activation Error")
            raise
    
    def create_subscription_sales_invoice(self, subscription, payment_txn):
        """Create Sales Invoice for subscription payment"""
        try:
            customer = frappe.get_doc("Customer", subscription.customer)
            
            # Check if invoice already exists for this subscription
            existing_invoice = frappe.db.get_value("Sales Invoice", {
                "custom_subscription_id": subscription.name,
                "custom_payment_reference": payment_txn.reference_id
            })
            
            if existing_invoice:
                return frappe.get_doc("Sales Invoice", existing_invoice)
            
            # Create new Sales Invoice
            invoice = frappe.new_doc("Sales Invoice")
            invoice.customer = subscription.customer
            invoice.company = subscription.company or frappe.defaults.get_user_default("company")
            invoice.posting_date = frappe.utils.nowdate()
            invoice.due_date = subscription.current_invoice_start or frappe.utils.nowdate()
            invoice.currency = subscription.currency or "ZMW"
            
            # Get subscription item
            item_code = self.get_subscription_item_code(subscription.subscription_plan)
            
            # Add subscription item
            invoice.append("items", {
                "item_code": item_code,
                "item_name": f"Subscription - {subscription.subscription_plan}",
                "description": f"Subscription service for {subscription.subscription_plan}",
                "qty": 1,
                "uom": "Nos",
                "rate": subscription.total,
                "amount": subscription.total
            })
            
            # Set custom fields
            invoice.custom_subscription_id = subscription.name
            invoice.custom_payment_reference = payment_txn.reference_id
            invoice.custom_payment_method = payment_txn.payment_method
            
            # Calculate taxes and totals
            invoice.calculate_taxes_and_totals()
            
            invoice.insert(ignore_permissions=True)
            invoice.submit()
            
            frappe.logger().info(f"Created Sales Invoice {invoice.name} for subscription {subscription.name}")
            
            return invoice
            
        except Exception as e:
            frappe.log_error(f"Error creating subscription sales invoice: {str(e)}", "Invoice Creation Error")
            raise
    
    def get_subscription_item_code(self, subscription_plan):
        """Get or create subscription item"""
        if not subscription_plan:
            return "SERVICE-001"  # Default service item
        
        # Try to get item from subscription plan
        try:
            plan = frappe.get_doc("Subscription Plan", subscription_plan)
            if plan.item:
                return plan.item
        except:
            pass
        
        # Create item code based on plan name
        item_code = f"SUB-{subscription_plan.replace(' ', '-').upper()}"
        
        if not frappe.db.exists("Item", item_code):
            item = frappe.new_doc("Item")
            item.item_code = item_code
            item.item_name = f"Subscription - {subscription_plan}"
            item.item_group = "Services"
            item.is_stock_item = 0
            item.stock_uom = "Nos"
            item.standard_rate = 0  # Will be set per subscription
            item.insert(ignore_permissions=True)
        
        return item_code
    
    def create_payment_for_invoice(self, invoice_name, payment_txn):
        """Create Payment Entry for Sales Invoice"""
        try:
            from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
            
            # Get payment entry from invoice
            payment_entry = get_payment_entry(dt="Sales Invoice", dn=invoice_name)
            
            # Update payment details
            payment_entry.payment_type = "Receive"
            payment_entry.paid_to = self.get_default_receivable_account()
            payment_entry.paid_amount = payment_txn.amount
            payment_entry.received_amount = payment_txn.amount
            payment_entry.reference_no = payment_txn.transaction_id or payment_txn.reference_id
            payment_entry.reference_date = frappe.utils.nowdate()
            
            # Set mode of payment based on payment method
            payment_entry.mode_of_payment = self.get_mode_of_payment(payment_txn.payment_method)
            
            # Set custom fields
            payment_entry.custom_payment_gateway = "ZoykTech"
            payment_entry.custom_gateway_reference = payment_txn.reference_id
            payment_entry.custom_is_subscription_payment = 1
            payment_entry.custom_subscription_id = payment_txn.reference_id.split('_')[1] if '_' in payment_txn.reference_id else None
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.logger().info(f"Created Payment Entry {payment_entry.name} for invoice {invoice_name}")
            
            return payment_entry
            
        except Exception as e:
            frappe.log_error(f"Error creating payment entry: {str(e)}", "Payment Entry Error")
            raise
    
    def get_mode_of_payment(self, payment_method):
        """Get mode of payment based on payment method"""
        if payment_method and 'mobile' in payment_method.lower():
            return "Mobile Money"
        elif payment_method and 'card' in payment_method.lower():
            return "Card"
        else:
            return "Electronic"
    
    def get_default_receivable_account(self):
        """Get default receivable account"""
        try:
            company = frappe.defaults.get_user_default("company")
            account = frappe.db.get_value("Company", company, "default_receivable_account")
            return account
        except:
            return "Debtors - " + frappe.defaults.get_global_default("company_abbr")
    
    def update_subscription_after_payment(self, subscription, sales_invoice, payment_entry, payment_link):
        """Update subscription after successful payment"""
        # Update subscription custom fields
        subscription.custom_payment_reference = payment_link.reference_id
        subscription.custom_payment_status = "Paid"
        subscription.custom_payment_transaction = payment_link.payment_transaction
        subscription.custom_last_payment_date = frappe.utils.nowdate()
        subscription.custom_last_invoice = sales_invoice.name
        subscription.custom_last_payment = payment_entry.name
        subscription.custom_payment_link = payment_link.name
        
        # Update subscription status to Active if it was Pending
        if subscription.status == "Pending":
            subscription.status = "Active"
        
        subscription.save(ignore_permissions=True)
        
        # Add invoice to subscription's invoices table
        if not subscription.invoices:
            subscription.invoices = []
        
        subscription.append("invoices", {
            "invoice": sales_invoice.name,
            "amount": sales_invoice.grand_total,
            "currency": sales_invoice.currency,
            "posting_date": sales_invoice.posting_date
        })
        
        subscription.save(ignore_permissions=True)
    
    def handle_failed_subscription_payment(self, subscription_name, payment_link_name):
        """Handle failed subscription payment"""
        subscription = frappe.get_doc("Subscription", subscription_name)
        
        subscription.custom_payment_status = "Failed"
        subscription.save(ignore_permissions=True)
        
        # Send failure notification
        self.send_payment_failure_notification(subscription)
    
    def handle_payment_timeout(self, subscription_name, payment_link_name, reference_id):
        """Handle payment timeout"""
        subscription = frappe.get_doc("Subscription", subscription_name)
        
        subscription.custom_payment_status = "Timed Out"
        subscription.save(ignore_permissions=True)
    
    def send_subscription_activated_notification(self, subscription, invoice):
        """Send subscription activation notification"""
        try:
            customer = frappe.get_doc("Customer", subscription.customer)
            
            if customer.email_id:
                frappe.sendmail(
                    recipients=customer.email_id,
                    subject=_("Subscription Activated - {0}").format(subscription.name),
                    message=f"""
Dear {customer.customer_name},

Your subscription has been activated successfully.

Subscription Details:
- Subscription ID: {subscription.name}
- Plan: {subscription.subscription_plan}
- Amount: {subscription.total} {subscription.currency}
- Start Date: {subscription.current_invoice_start}
- End Date: {subscription.current_invoice_end}

Invoice Details:
- Invoice Number: {invoice.name}
- Amount: {invoice.grand_total} {invoice.currency}
- Date: {invoice.posting_date}

Thank you for your subscription!

Best regards,
Subscription Team
"""
                )
        except Exception as e:
            frappe.log_error(f"Error sending activation email: {str(e)}", "Email Error")
    
    def send_payment_failure_notification(self, subscription):
        """Send payment failure notification"""
        try:
            customer = frappe.get_doc("Customer", subscription.customer)
            
            if customer.email_id:
                frappe.sendmail(
                    recipients=customer.email_id,
                    subject=_("Subscription Payment Failed - {0}").format(subscription.name),
                    message=f"""
Dear {customer.customer_name},

We were unable to process the payment for your subscription.

Subscription: {subscription.subscription_plan}
Amount: {subscription.total} {subscription.currency}

Please update your payment method or contact support to complete your subscription.

Best regards,
Subscription Team
"""
                )
        except Exception as e:
            frappe.log_error(f"Error sending failure email: {str(e)}", "Email Error")
    
    # Webhook handler for subscription payments
    def handle_subscription_webhook(self, reference_id, payment_data):
        """Handle subscription payment webhook"""
        try:
            # Find the payment transaction
            payment_txn = frappe.get_doc("Payment Transaction", reference_id)
            
            # Update payment transaction
            payment_txn.status = "Completed"
            payment_txn.transaction_id = payment_data.get("transaction_id")
            payment_txn.payment_completed = datetime.now()
            payment_txn.save(ignore_permissions=True)
            
            # Find associated payment link
            payment_link = frappe.get_doc("Payment Link", {"payment_transaction": payment_txn.name})
            
            # Update payment link
            payment_link.status = "Paid"
            payment_link.save(ignore_permissions=True)
            
            # Get subscription from payment link
            subscription_name = payment_link.linked_docname
            
            # Process successful payment
            return self.process_successful_subscription_payment(
                subscription_name,
                payment_link.name,
                payment_txn.name
            )
            
        except Exception as e:
            frappe.log_error(f"Error handling subscription webhook: {str(e)}", "Subscription Webhook Error")
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to process subscription webhook")
            }