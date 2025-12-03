# payment_link.py

from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.model.document import Document


class PaymentLink(Document):
	def validate(self):
		self.validate_expiry_date()
		self.validate_amount()

	def before_insert(self):
		self.set_default_expiry()

	def validate_expiry_date(self):
		"""Validate expiry date is in the future"""
		if self.expiry_date and self.expiry_date < datetime.now():
			frappe.throw(_("Expiry date must be in the future"))

	def validate_amount(self):
		"""Validate payment amount"""
		if self.amount <= 0:
			frappe.throw(_("Payment amount must be greater than 0"))

	def set_default_expiry(self):
		"""Set default expiry date if not provided"""
		if not self.expiry_date:
			self.expiry_date = datetime.now() + timedelta(days=7)

	def is_expired(self):
		"""Check if payment link has expired"""
		if not self.expiry_date:
			return False
		return datetime.now() > self.expiry_date

	def mark_as_paid(self, payment_transaction=None):
		"""Mark payment link as paid"""
		self.status = "Paid"
		if payment_transaction:
			self.payment_transaction = payment_transaction
		self.save()

	def mark_as_failed(self):
		"""Mark payment link as failed"""
		self.status = "Failed"
		self.save()

	def mark_as_cancelled(self):
		"""Mark payment link as cancelled"""
		self.status = "Cancelled"
		self.save()


@frappe.whitelist()
def create_payment_link(doctype, docname, amount, currency="ZMW", description=None, expiry_days=7):
	"""Create a new payment link"""
	try:
		# Generate unique reference
		reference_id = f"PL_{datetime.now().strftime('%Y%m%d%H%M%S')}_{frappe.generate_hash(length=6)}"

		# Create payment link
		payment_link = frappe.new_doc("Payment Link")
		payment_link.reference_id = reference_id
		payment_link.linked_doctype = doctype
		payment_link.linked_docname = docname
		payment_link.amount = amount
		payment_link.currency = currency
		payment_link.description = description
		payment_link.expiry_date = datetime.now() + timedelta(days=expiry_days)
		payment_link.status = "Pending"

		payment_link.insert(ignore_permissions=True)

		return {
			"success": True,
			"payment_link": payment_link.name,
			"reference_id": reference_id,
			"message": _("Payment link created successfully"),
		}

	except Exception as e:
		frappe.log_error(f"Error creating payment link: {str(e)}", "Payment Link Creation")
		return {"success": False, "error": str(e), "message": _("Failed to create payment link")}


@frappe.whitelist()
def get_payment_link_status(reference_id):
	"""Get payment link status"""
	try:
		payment_link = frappe.get_doc("Payment Link", reference_id)

		return {
			"success": True,
			"status": payment_link.status,
			"amount": payment_link.amount,
			"currency": payment_link.currency,
			"expiry_date": payment_link.expiry_date,
			"is_expired": payment_link.is_expired(),
		}

	except frappe.DoesNotExistError:
		return {"success": False, "error": "Payment link not found", "message": _("Payment link not found")}


@frappe.whitelist()
def cancel_payment_link(reference_id):
	"""Cancel a payment link"""
	try:
		payment_link = frappe.get_doc("Payment Link", reference_id)

		if payment_link.status == "Paid":
			return {"success": False, "message": _("Cannot cancel a paid payment link")}

		payment_link.mark_as_cancelled()

		return {"success": True, "message": _("Payment link cancelled successfully")}

	except Exception as e:
		return {"success": False, "error": str(e), "message": _("Failed to cancel payment link")}
