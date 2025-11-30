import frappe
from frappe.model.document import Document
from frappe import _
import json
from datetime import datetime

class PaymentTransaction(Document):
    def validate(self):
        self.validate_amount()
        self.update_linked_document_status()
    
    def before_insert(self):
        self.set_default_values()
    
    def validate_amount(self):
        """Validate payment amount"""
        if self.amount <= 0:
            frappe.throw(_("Payment amount must be greater than 0"))
    
    def set_default_values(self):
        """Set default values for new transaction"""
        if not self.payment_initiated:
            self.payment_initiated = datetime.now()
    
    def update_linked_document_status(self):
        """Update status of linked document when payment is completed"""
        if self.status == "Completed" and self.reference_id:
            try:
                # Check if this payment is linked to any document
                payment_links = frappe.get_all("Payment Link",
                    filters={"payment_transaction": self.name},
                    fields=["linked_doctype", "linked_docname"])
                
                for link in payment_links:
                    self.update_document_payment_status(link.linked_doctype, link.linked_docname)
                    
            except Exception as e:
                frappe.log_error(f"Error updating linked document: {str(e)}", "Payment Integration")
    
    def update_document_payment_status(self, doctype, docname):
        """Update payment status for various ERPNext documents"""
        try:
            if doctype == "Sales Invoice":
                self.update_sales_invoice_payment(docname)
            elif doctype == "Purchase Invoice":
                self.update_purchase_invoice_payment(docname)
            elif doctype == "Sales Order":
                self.update_sales_order_payment(docname)
            elif doctype == "Payment Entry":
                self.update_payment_entry(docname)
                
        except Exception as e:
            frappe.log_error(f"Error updating {doctype} {docname}: {str(e)}", "Payment Status Update")
    
    def update_sales_invoice_payment(self, invoice_name):
        """Update Sales Invoice with payment"""
        try:
            from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
            
            invoice = frappe.get_doc("Sales Invoice", invoice_name)
            
            # Create Payment Entry against Sales Invoice
            payment_entry = get_payment_entry(dt="Sales Invoice", dn=invoice_name)
            payment_entry.payment_type = "Receive"
            payment_entry.reference_no = self.transaction_id or self.reference_id
            payment_entry.reference_date = datetime.now().date()
            payment_entry.paid_amount = self.amount
            payment_entry.received_amount = self.amount
            
            # Set mode of payment based on payment method
            payment_entry.mode_of_payment = self.get_mode_of_payment()
            
            # Set custom field for gateway reference
            payment_entry.custom_gateway_reference = self.name
            payment_entry.custom_payment_method = self.payment_method
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_("Payment Entry {0} created against Sales Invoice {1}").format(
                payment_entry.name, invoice_name))
                
        except Exception as e:
            frappe.log_error(f"Error creating payment entry for Sales Invoice: {str(e)}", "Payment Entry Error")
            raise
    
    def update_purchase_invoice_payment(self, invoice_name):
        """Update Purchase Invoice with payment"""
        try:
            from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
            
            # Create Payment Entry against Purchase Invoice
            payment_entry = get_payment_entry(dt="Purchase Invoice", dn=invoice_name)
            payment_entry.payment_type = "Pay"
            payment_entry.reference_no = self.transaction_id or self.reference_id
            payment_entry.reference_date = datetime.now().date()
            payment_entry.mode_of_payment = self.get_mode_of_payment()
            payment_entry.custom_gateway_reference = self.name
            payment_entry.custom_payment_method = self.payment_method
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_("Payment Entry {0} created against Purchase Invoice {1}").format(
                payment_entry.name, invoice_name))
                
        except Exception as e:
            frappe.log_error(f"Error creating payment entry for Purchase Invoice: {str(e)}", "Payment Entry Error")
            raise
    
    def update_sales_order_payment(self, order_name):
        """Update Sales Order with advance payment"""
        try:
            from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
            
            order = frappe.get_doc("Sales Order", order_name)
            
            # Create Payment Entry for advance payment
            payment_entry = get_payment_entry(dt="Sales Order", dn=order_name)
            payment_entry.payment_type = "Receive"
            payment_entry.reference_no = self.transaction_id or self.reference_id
            payment_entry.reference_date = datetime.now().date()
            payment_entry.mode_of_payment = self.get_mode_of_payment()
            payment_entry.custom_gateway_reference = self.name
            payment_entry.custom_payment_method = self.payment_method
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_("Advance Payment Entry {0} created for Sales Order {1}").format(
                payment_entry.name, order_name))
                
        except Exception as e:
            frappe.log_error(f"Error creating advance payment for Sales Order: {str(e)}", "Advance Payment Error")
            raise
    
    def update_payment_entry(self, payment_entry_name):
        """Update existing Payment Entry"""
        try:
            payment_entry = frappe.get_doc("Payment Entry", payment_entry_name)
            payment_entry.reference_no = self.transaction_id or self.reference_id
            payment_entry.custom_gateway_reference = self.name
            payment_entry.custom_payment_method = self.payment_method
            payment_entry.save(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(f"Error updating Payment Entry: {str(e)}", "Payment Entry Update")
    
    def get_mode_of_payment(self):
        """Get or create mode of payment based on payment method"""
        if self.payment_method and 'mobile' in self.payment_method.lower():
            mode_name = "Mobile Money"
        elif self.payment_method and 'card' in self.payment_method.lower():
            mode_name = "Card"
        else:
            mode_name = "Electronic"
        
        # Create mode of payment if it doesn't exist
        if not frappe.db.exists("Mode of Payment", mode_name):
            frappe.get_doc({
                "doctype": "Mode of Payment",
                "mode_of_payment": mode_name,
                "type": "Phone" if "mobile" in mode_name.lower() else "Card"
            }).insert(ignore_permissions=True)
        
        return mode_name
    
    def mark_as_completed(self, transaction_id=None):
        """Mark transaction as completed"""
        self.status = "Completed"
        if transaction_id:
            self.transaction_id = transaction_id
        self.payment_completed = datetime.now()
        self.save()
    
    def mark_as_failed(self, failure_reason=None):
        """Mark transaction as failed"""
        self.status = "Failed"
        if failure_reason:
            self.failure_reason = failure_reason
        self.save()

@frappe.whitelist()
def create_payment_transaction(payment_data):
    """Create a new payment transaction"""
    try:
        if isinstance(payment_data, str):
            payment_data = json.loads(payment_data)
        
        # Check if transaction already exists
        if frappe.db.exists("Payment Transaction", payment_data.get('reference')):
            return {
                "success": False,
                "message": _("Payment transaction already exists")
            }
        
        # Create transaction
        transaction = frappe.new_doc("Payment Transaction")
        transaction.reference_id = payment_data.get('reference')
        transaction.amount = payment_data.get('amount', 0)
        transaction.currency = payment_data.get('currency', 'ZMW')
        transaction.status = "Pending"
        transaction.customer_email = payment_data.get('customer_email')
        transaction.customer_phone = payment_data.get('customer_phone')
        transaction.payment_method = payment_data.get('payment_method')
        transaction.gateway_response = json.dumps(payment_data, indent=2)
        
        transaction.insert(ignore_permissions=True)
        
        return {
            "success": True,
            "transaction": transaction.name,
            "message": _("Payment transaction created successfully")
        }
    
    except Exception as e:
        frappe.log_error(f"Error creating payment transaction: {str(e)}", "Payment Transaction Creation")
        return {
            "success": False,
            "error": str(e),
            "message": _("Failed to create payment transaction")
        }

@frappe.whitelist()
def update_payment_status(reference_id, status, transaction_id=None, failure_reason=None):
    """Update payment transaction status"""
    try:
        transaction = frappe.get_doc("Payment Transaction", reference_id)
        
        if status == "Completed":
            transaction.mark_as_completed(transaction_id)
        elif status == "Failed":
            transaction.mark_as_failed(failure_reason)
        else:
            transaction.status = status
            transaction.save()
        
        return {
            "success": True,
            "message": _("Payment status updated successfully")
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }