import frappe
from frappe import _
from typing import Dict, Optional, List
from .zoyktech_client import ZoykTechClient
from ..utils.helpers import create_payment_reference, get_payment_gateway_settings
import json
from datetime import datetime, timedelta

class PaymentIntegration:
    """Complete Payment Integration Engine for ERPNext"""
    
    def __init__(self, gateway_client=None):
        self.client = gateway_client or ZoykTechClient()
        self.settings = get_payment_gateway_settings()
    
    def create_payment_request(self, doctype: str, docname: str, payment_method: str = None, **kwargs) -> Dict:
        """
        Create payment request for any ERPNext document
        
        Args:
            doctype: Document type
            docname: Document name  
            payment_method: Preferred payment method
            **kwargs: Additional arguments
            
        Returns:
            Payment request response
        """
        try:
            # Get document and validate
            doc = frappe.get_doc(doctype, docname)
            self.validate_document_for_payment(doctype, doc)
            
            # Create payment reference
            reference_id = self.generate_payment_reference(doctype, docname)
            
            # Create payment link
            payment_link = self.create_payment_link(doctype, docname, reference_id, doc, payment_method)
            
            # Prepare payment data
            payment_data = self.prepare_payment_data(doctype, doc, reference_id, payment_method, kwargs)
            
            # Initiate payment with gateway based on method
            if payment_method and payment_method.lower() in ['mtn', 'airtel']:
                gateway_response = self.process_mobile_payment(payment_data, payment_method)
            else:
                gateway_response = self.client.initiate_payment(payment_data)
            
            # Update payment link with response
            self.update_payment_link_with_response(payment_link, gateway_response)
            
            # Create payment transaction record
            payment_txn = self.create_payment_transaction(reference_id, payment_data, gateway_response)
            
            return {
                "success": True,
                "payment_url": gateway_response.get("payment_url"),
                "reference_id": reference_id,
                "payment_link": payment_link,
                "payment_transaction": payment_txn,
                "gateway_response": gateway_response,
                "message": _("Payment request created successfully")
            }
            
        except Exception as e:
            frappe.log_error(f"Error creating payment request: {str(e)}", "Payment Request Error")
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to create payment request")
            }
    
    def validate_document_for_payment(self, doctype: str, doc) -> bool:
        """Validate if document can be paid"""
        valid_doctypes = ["Sales Invoice", "Purchase Invoice", "Sales Order", "Payment Entry"]
        
        if doctype not in valid_doctypes:
            frappe.throw(_(f"Payment not supported for {doctype}"))
        
        if doctype == "Sales Invoice":
            if doc.docstatus != 1:
                frappe.throw(_("Sales Invoice must be submitted before payment"))
            if doc.status == "Paid":
                frappe.throw(_("Sales Invoice is already paid"))
            if doc.outstanding_amount <= 0:
                frappe.throw(_("No outstanding amount to pay"))
        
        elif doctype == "Purchase Invoice":
            if doc.docstatus != 1:
                frappe.throw(_("Purchase Invoice must be submitted before payment"))
            if doc.outstanding_amount <= 0:
                frappe.throw(_("No outstanding amount to pay"))
        
        elif doctype == "Sales Order":
            if doc.docstatus != 1:
                frappe.throw(_("Sales Order must be submitted before payment"))
        
        return True
    
    def generate_payment_reference(self, doctype: str, docname: str) -> str:
        """Generate unique payment reference"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = frappe.generate_hash(length=6)
        return f"{doctype[:3]}_{docname}_{timestamp}_{random_str}"
    
    def create_payment_link(self, doctype: str, docname: str, reference_id: str, doc, payment_method: str = None) -> str:
        """Create payment link document"""
        payment_link = frappe.new_doc("Payment Link")
        payment_link.reference_id = reference_id
        payment_link.linked_doctype = doctype
        payment_link.linked_docname = docname
        payment_link.amount = self.get_payable_amount(doctype, doc)
        payment_link.currency = doc.currency or "ZMW"
        payment_link.status = "Pending"
        payment_link.payment_method = payment_method
        
        # Set expiry date (default 24 hours)
        payment_link.expiry_date = datetime.now() + timedelta(hours=24)
        
        # Add customer/supplier details
        self.add_party_details(payment_link, doc)
        
        payment_link.insert(ignore_permissions=True)
        
        return payment_link.name
    
    def get_payable_amount(self, doctype: str, doc) -> float:
        """Get payable amount based on document type"""
        if doctype == "Sales Invoice":
            return doc.outstanding_amount
        elif doctype == "Purchase Invoice":
            return doc.outstanding_amount
        elif doctype == "Sales Order":
            # For sales order, allow partial payments
            return doc.grand_total - (doc.advance_paid or 0)
        elif doctype == "Payment Entry":
            return doc.paid_amount
        else:
            return doc.grand_total
    
    def add_party_details(self, payment_link, doc):
        """Add customer/supplier details to payment link"""
        if hasattr(doc, 'customer') and doc.customer:
            payment_link.customer = doc.customer
            payment_link.customer_name = doc.customer_name
        
        if hasattr(doc, 'supplier') and doc.supplier:
            payment_link.supplier = doc.supplier
            payment_link.customer_name = doc.supplier_name
        
        # Contact information
        payment_link.customer_email = self.get_contact_email(doc)
        payment_link.customer_phone = self.get_contact_phone(doc)
    
    def get_contact_email(self, doc) -> Optional[str]:
        """Extract contact email from document"""
        email_fields = ['contact_email', 'customer_email', 'email_id', 'owner']
        for field in email_fields:
            if hasattr(doc, field) and getattr(doc, field):
                return getattr(doc, field)
        return None
    
    def get_contact_phone(self, doc) -> Optional[str]:
        """Extract contact phone from document"""
        phone_fields = ['contact_phone', 'customer_phone', 'mobile_no', 'phone']
        for field in phone_fields:
            if hasattr(doc, field) and getattr(doc, field):
                return getattr(doc, field)
        return None
    
    def prepare_payment_data(self, doctype: str, doc, reference_id: str, payment_method: str = None, kwargs: dict = None) -> Dict:
        """Prepare payment data for gateway"""
        amount = self.get_payable_amount(doctype, doc)
        kwargs = kwargs or {}
        
        payment_data = {
            "amount": amount,
            "currency": doc.currency or "ZMW",
            "reference": reference_id,
            "customer_email": self.get_contact_email(doc),
            "customer_phone": self.get_contact_phone(doc),
            "metadata": {
                "doctype": doctype,
                "docname": doc.name,
                "company": doc.company if hasattr(doc, 'company') else frappe.defaults.get_user_default("company"),
                "customer": doc.customer if hasattr(doc, 'customer') else None,
                "supplier": doc.supplier if hasattr(doc, 'supplier') else None,
                "created_by": frappe.session.user
            }
        }
        
        if payment_method:
            payment_data["payment_method"] = payment_method
        
        # Add custom callback URL if provided
        if kwargs.get('callback_url'):
            payment_data['callback_url'] = kwargs['callback_url']
        
        return payment_data
    
    def process_mobile_payment(self, payment_data: Dict, network: str) -> Dict:
        """Process mobile money payment specifically"""
        mobile_data = {
            "amount": payment_data['amount'],
            "network": network,
            "phone_number": payment_data['customer_phone'],
            "reference": payment_data['reference'],
            "customer_email": payment_data['customer_email'],
            "metadata": payment_data.get('metadata', {})
        }
        
        return self.client.process_mobile_money(mobile_data)
    
    def update_payment_link_with_response(self, payment_link_name: str, gateway_response: Dict):
        """Update payment link with gateway response"""
        payment_link = frappe.get_doc("Payment Link", payment_link_name)
        payment_link.payment_url = gateway_response.get("payment_url")
        payment_link.save(ignore_permissions=True)
    
    def create_payment_transaction(self, reference_id: str, payment_data: Dict, gateway_response: Dict) -> str:
        """Create payment transaction record"""
        payment_txn = frappe.new_doc("Payment Transaction")
        payment_txn.reference_id = reference_id
        payment_txn.amount = payment_data['amount']
        payment_txn.currency = payment_data['currency']
        payment_txn.status = "Pending"
        payment_txn.customer_email = payment_data['customer_email']
        payment_txn.customer_phone = payment_data['customer_phone']
        payment_txn.payment_initiated = datetime.now()
        payment_txn.gateway_response = json.dumps(gateway_response, indent=2)
        
        payment_txn.insert(ignore_permissions=True)
        
        return payment_txn.name
    
    def process_successful_payment(self, reference_id: str, gateway_data: Dict) -> Dict:
        """Process successful payment and update all linked documents"""
        try:
            # Update payment transaction
            payment_txn = self.update_payment_transaction(reference_id, gateway_data)
            
            # Update payment link
            self.update_payment_link_status(reference_id, "Paid", payment_txn.name)
            
            # Update linked ERPNext documents
            self.update_linked_erpnext_documents(reference_id, payment_txn)
            
            frappe.db.commit()
            
            return {
                "success": True,
                "payment_transaction": payment_txn.name,
                "message": _("Payment processed successfully")
            }
            
        except Exception as e:
            frappe.db.rollback()
            frappe.log_error(f"Error processing successful payment: {str(e)}", "Payment Processing Error")
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to process payment")
            }
    
    def update_payment_transaction(self, reference_id: str, gateway_data: Dict):
        """Update payment transaction with successful payment details"""
        try:
            payment_txn = frappe.get_doc("Payment Transaction", reference_id)
        except frappe.DoesNotExistError:
            # Create new if doesn't exist (for direct webhook calls)
            payment_txn = frappe.new_doc("Payment Transaction")
            payment_txn.reference_id = reference_id
        
        payment_txn.amount = gateway_data.get("amount", 0)
        payment_txn.currency = gateway_data.get("currency", "ZMW")
        payment_txn.status = "Completed"
        payment_txn.transaction_id = gateway_data.get("transaction_id")
        payment_txn.payment_method = gateway_data.get("payment_method")
        payment_txn.customer_email = gateway_data.get("customer_email")
        payment_txn.customer_phone = gateway_data.get("customer_phone")
        payment_txn.gateway_response = json.dumps(gateway_data, indent=2)
        payment_txn.payment_completed = datetime.now()
        
        if not payment_txn.get('name'):
            payment_txn.insert(ignore_permissions=True)
        else:
            payment_txn.save(ignore_permissions=True)
        
        return payment_txn
    
    def update_payment_link_status(self, reference_id: str, status: str, payment_txn_name: str = None):
        """Update payment link status"""
        payment_links = frappe.get_all("Payment Link",
            filters={"reference_id": reference_id},
            fields=["name"])
        
        for link in payment_links:
            payment_link = frappe.get_doc("Payment Link", link.name)
            payment_link.status = status
            if payment_txn_name:
                payment_link.payment_transaction = payment_txn_name
            payment_link.save(ignore_permissions=True)
    
    def update_linked_erpnext_documents(self, reference_id: str, payment_txn):
        """Update all linked ERPNext documents with payment"""
        payment_links = frappe.get_all("Payment Link",
            filters={"reference_id": reference_id, "status": "Paid"},
            fields=["linked_doctype", "linked_docname"])
        
        for link in payment_links:
            try:
                if link.linked_doctype == "Sales Invoice":
                    self.update_sales_invoice_payment(link.linked_docname, payment_txn)
                elif link.linked_doctype == "Purchase Invoice":
                    self.update_purchase_invoice_payment(link.linked_docname, payment_txn)
                elif link.linked_doctype == "Sales Order":
                    self.update_sales_order_payment(link.linked_docname, payment_txn)
                
                frappe.db.commit()
                
            except Exception as e:
                frappe.db.rollback()
                frappe.log_error(f"Error updating {link.linked_doctype} {link.linked_docname}: {str(e)}", "Document Update Error")
    
    def update_sales_invoice_payment(self, invoice_name: str, payment_txn):
        """Create Payment Entry for Sales Invoice"""
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
        
        try:
            payment_entry = get_payment_entry(dt="Sales Invoice", dn=invoice_name)
            payment_entry.payment_type = "Receive"
            payment_entry.reference_no = payment_txn.transaction_id or payment_txn.reference_id
            payment_entry.reference_date = datetime.now().date()
            
            # Set mode of payment based on payment method
            payment_entry.mode_of_payment = self.get_mode_of_payment(payment_txn.payment_method)
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_("Payment Entry {0} created for Sales Invoice {1}").format(
                payment_entry.name, invoice_name))
                
        except Exception as e:
            frappe.log_error(f"Error creating payment entry for Sales Invoice: {str(e)}", "Payment Entry Error")
            raise
    
    def update_purchase_invoice_payment(self, invoice_name: str, payment_txn):
        """Create Payment Entry for Purchase Invoice"""
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
        
        try:
            payment_entry = get_payment_entry(dt="Purchase Invoice", dn=invoice_name)
            payment_entry.payment_type = "Pay"
            payment_entry.reference_no = payment_txn.transaction_id or payment_txn.reference_id
            payment_entry.reference_date = datetime.now().date()
            payment_entry.mode_of_payment = self.get_mode_of_payment(payment_txn.payment_method)
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_("Payment Entry {0} created for Purchase Invoice {1}").format(
                payment_entry.name, invoice_name))
                
        except Exception as e:
            frappe.log_error(f"Error creating payment entry for Purchase Invoice: {str(e)}", "Payment Entry Error")
            raise
    
    def update_sales_order_payment(self, order_name: str, payment_txn):
        """Create advance payment for Sales Order"""
        from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
        
        try:
            payment_entry = get_payment_entry(dt="Sales Order", dn=order_name)
            payment_entry.payment_type = "Receive"
            payment_entry.reference_no = payment_txn.transaction_id or payment_txn.reference_id
            payment_entry.reference_date = datetime.now().date()
            payment_entry.mode_of_payment = self.get_mode_of_payment(payment_txn.payment_method)
            
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()
            
            frappe.msgprint(_("Advance Payment Entry {0} created for Sales Order {1}").format(
                payment_entry.name, order_name))
                
        except Exception as e:
            frappe.log_error(f"Error creating advance payment for Sales Order: {str(e)}", "Advance Payment Error")
            raise
    
    def get_mode_of_payment(self, payment_method: str) -> str:
        """Get or create mode of payment based on payment method"""
        if payment_method.lower() in ['mtn', 'airtel']:
            mode_name = "Mobile Money"
        elif payment_method.lower() == 'card':
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
    
    # Additional utility methods
    def get_payment_status(self, reference_id: str) -> Dict:
        """Get payment status from gateway"""
        try:
            gateway_response = self.client.verify_payment(reference_id)
            return {
                "success": True,
                "status": gateway_response.get("status"),
                "gateway_response": gateway_response
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status": "Unknown"
            }
    
    def cancel_payment_request(self, reference_id: str) -> Dict:
        """Cancel a payment request"""
        try:
            # Update payment link status
            self.update_payment_link_status(reference_id, "Cancelled")
            
            # Update payment transaction if exists
            try:
                payment_txn = frappe.get_doc("Payment Transaction", reference_id)
                payment_txn.status = "Cancelled"
                payment_txn.save(ignore_permissions=True)
            except frappe.DoesNotExistError:
                pass
            
            return {
                "success": True,
                "message": _("Payment request cancelled successfully")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": _("Failed to cancel payment request")
            }