# routes.py

import frappe
from frappe import whitelist

from ..utils.subscription_payment_handler import SubscriptionPaymentHandler
from .payment_integration import PaymentIntegration
from .zoyktech_client import ZoykTechClient


@whitelist(allow_guest=True)
def get_payment_methods():
	"""Get available payment methods"""
	client = ZoykTechClient()
	return client.get_payment_methods()


@whitelist()
def create_payment(doctype, docname, payment_method=None):
	"""Create payment request for document"""
	integration = PaymentIntegration()
	return integration.create_payment_request(doctype, docname, payment_method)


@whitelist()
def get_payment_status(reference_id):
	"""Get payment status"""
	integration = PaymentIntegration()
	return integration.get_payment_status(reference_id)


@whitelist()
def cancel_payment(reference_id):
	"""Cancel payment request"""
	integration = PaymentIntegration()
	return integration.cancel_payment_request(reference_id)


@whitelist()
def process_refund(transaction_id, amount, reason=""):
	"""Process refund for transaction"""
	client = ZoykTechClient()
	refund_data = {"transaction_id": transaction_id, "amount": amount, "reason": reason}
	return client.refund_payment(refund_data)


@whitelist(allow_guest=True)
def payment_success_page(reference_id):
	"""Payment success page for customers"""
	try:
		payment_txn = frappe.get_doc("Payment Transaction", reference_id)
		return {"success": True, "payment": payment_txn, "message": "Payment completed successfully"}
	except Exception as e:
		return {"success": False, "error": str(e)}


@whitelist(allow_guest=True)
def payment_failure_page(reference_id):
	"""Payment failure page for customers"""
	try:
		payment_txn = frappe.get_doc("Payment Transaction", reference_id)
		return {"success": False, "payment": payment_txn, "message": "Payment failed"}
	except Exception as e:
		return {"success": False, "error": str(e)}


# Subscription Payment Routes
@whitelist()
def create_subscription_payment(subscription_name):
	"""API endpoint to create subscription payment"""
	handler = SubscriptionPaymentHandler()
	return handler.create_immediate_subscription_payment(subscription_name)


@whitelist()
def get_subscription_payment_status(subscription_name):
	"""Get payment status for a subscription"""
	subscription = frappe.get_doc("Subscription", subscription_name)

	if not subscription.custom_payment_reference:
		return {"success": False, "message": "No payment reference found"}

	integration = PaymentIntegration()
	return integration.get_payment_status(subscription.custom_payment_reference)


@whitelist()
def retry_subscription_payment(subscription_name):
	"""Retry failed subscription payment"""
	handler = SubscriptionPaymentHandler()
	return handler.create_immediate_subscription_payment(subscription_name)


@whitelist()
def cancel_subscription_payment(subscription_name):
	"""Cancel pending subscription payment"""
	try:
		subscription = frappe.get_doc("Subscription", subscription_name)

		if not subscription.custom_payment_link:
			return {"success": False, "message": "No active payment link found"}

		payment_link = frappe.get_doc("Payment Link", subscription.custom_payment_link)
		payment_link.status = "Cancelled"
		payment_link.save(ignore_permissions=True)

		subscription.custom_payment_status = "Cancelled"
		subscription.save(ignore_permissions=True)

		return {"success": True, "message": _("Subscription payment cancelled successfully")}

	except Exception as e:
		return {"success": False, "error": str(e), "message": _("Failed to cancel subscription payment")}
