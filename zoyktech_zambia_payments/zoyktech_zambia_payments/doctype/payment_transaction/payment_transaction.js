frappe.ui.form.on("Payment Transaction", {
	refresh: function (frm) {
		// Add custom buttons
		add_custom_buttons(frm);

		// Show gateway response
		show_gateway_response(frm);

		// Show status information
		show_status_info(frm);
	},

	reference_id: function (frm) {
		// Auto-generate reference ID if not provided
		if (!frm.doc.reference_id) {
			generate_reference_id(frm);
		}
	},
});

function add_custom_buttons(frm) {
	// Add check status button for pending transactions
	if (frm.doc.status === "Pending") {
		frm.add_custom_button(__("Check Status"), function () {
			check_payment_status(frm);
		});
	}

	// Add refund button for completed transactions
	if (frm.doc.status === "Completed") {
		frm.add_custom_button(__("Process Refund"), function () {
			process_refund(frm);
		});
	}

	// Add view payment link button
	if (frm.doc.reference_id) {
		frm.add_custom_button(__("View Payment Link"), function () {
			view_payment_link(frm);
		});
	}

	// Add retry button for failed transactions
	if (frm.doc.status === "Failed") {
		frm.add_custom_button(__("Retry Payment"), function () {
			retry_payment(frm);
		});
	}

	// Add create payment entry button
	if (frm.doc.status === "Completed" && !frm.doc.__islocal) {
		frm.add_custom_button(__("Create Payment Entry"), function () {
			create_payment_entry(frm);
		});
	}
}

function show_gateway_response(frm) {
	if (frm.doc.gateway_response) {
		try {
			const response = JSON.parse(frm.doc.gateway_response);
			const formatted_response = JSON.stringify(response, null, 2);

			const response_html = `
                <div class="gateway-response-section" style="margin: 15px 0;">
                    <h5>${__("Gateway Response")}</h5>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto; font-size: 12px;">${formatted_response}</pre>
                </div>
            `;

			frm.fields_dict.gateway_response.$wrapper.html(response_html);
		} catch (e) {
			// If not JSON, show as plain text
			frm.fields_dict.gateway_response.$wrapper.html(`
                <div class="gateway-response-section">
                    <h5>${__("Gateway Response")}</h5>
                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto;">${
						frm.doc.gateway_response
					}</pre>
                </div>
            `);
		}
	}
}

function show_status_info(frm) {
	let status_info = "";
	let alert_class = "";

	switch (frm.doc.status) {
		case "Completed":
			status_info = `
                <div class="alert alert-success">
                    <h6>${__("Payment Completed")}</h6>
                    <p>${__(
						"This payment has been successfully processed and the funds have been received."
					)}</p>
                    ${
						frm.doc.transaction_id
							? `<p><strong>${__("Transaction ID:")}</strong> ${
									frm.doc.transaction_id
							  }</p>`
							: ""
					}
                    ${
						frm.doc.payment_completed
							? `<p><strong>${__(
									"Completed:"
							  )}</strong> ${frappe.datetime.str_to_user(
									frm.doc.payment_completed
							  )}</p>`
							: ""
					}
                </div>
            `;
			break;

		case "Pending":
			status_info = `
                <div class="alert alert-warning">
                    <h6>${__("Payment Pending")}</h6>
                    <p>${__(
						"This payment is being processed. Please check back later for updates."
					)}</p>
                    ${
						frm.doc.payment_initiated
							? `<p><strong>${__(
									"Initiated:"
							  )}</strong> ${frappe.datetime.str_to_user(
									frm.doc.payment_initiated
							  )}</p>`
							: ""
					}
                </div>
            `;
			break;

		case "Failed":
			status_info = `
                <div class="alert alert-danger">
                    <h6>${__("Payment Failed")}</h6>
                    <p>${__("This payment could not be processed.")}</p>
                    ${
						frm.doc.failure_reason
							? `<p><strong>${__("Reason:")}</strong> ${frm.doc.failure_reason}</p>`
							: ""
					}
                </div>
            `;
			break;

		case "Refunded":
			status_info = `
                <div class="alert alert-info">
                    <h6>${__("Payment Refunded")}</h6>
                    <p>${__("This payment has been refunded to the customer.")}</p>
                </div>
            `;
			break;
	}

	if (status_info) {
		frm.dashboard.add_indicator(__("Payment Status"), status_info);
	}
}

function generate_reference_id(frm) {
	const timestamp = new Date().getTime();
	const random = Math.random().toString(36).substring(2, 8).toUpperCase();
	frm.set_value("reference_id", `TXN_${timestamp}_${random}`);
}

function check_payment_status(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.get_payment_status",
		args: {
			reference_id: frm.doc.reference_id,
		},
		callback: function (response) {
			if (response.message.success) {
				const status = response.message.status;

				if (status !== frm.doc.status) {
					frappe.msgprint({
						title: __("Status Updated"),
						indicator: "green",
						message: __("Payment status has been updated from {0} to {1}", [
							frm.doc.status,
							status,
						]),
					});
					frm.reload_doc();
				} else {
					frappe.msgprint({
						title: __("Status Check"),
						indicator: "blue",
						message: __("Payment status is still {0}", [status]),
					});
				}
			} else {
				frappe.msgprint({
					title: __("Status Check Failed"),
					indicator: "red",
					message: response.message.message || __("Failed to check payment status"),
				});
			}
		},
	});
}

function process_refund(frm) {
	frappe.prompt(
		{
			fieldname: "refund_amount",
			label: __("Refund Amount"),
			fieldtype: "Currency",
			reqd: 1,
			default: frm.doc.amount,
			description: __("Enter amount to refund (cannot exceed original amount)"),
		},
		(values) => {
			if (values.refund_amount > frm.doc.amount) {
				frappe.msgprint({
					title: __("Invalid Amount"),
					indicator: "red",
					message: __("Refund amount cannot exceed original amount"),
				});
				return;
			}

			frappe.prompt(
				{
					fieldname: "refund_reason",
					label: __("Refund Reason"),
					fieldtype: "Select",
					options:
						"\nCustomer Request\nDuplicate Payment\nService Not Provided\nTechnical Error\nFraudulent Transaction\nOther",
					reqd: 1,
					default: "Customer Request",
				},
				(reason_values) => {
					frappe.call({
						method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_refund.payment_refund.create_refund",
						args: {
							payment_reference: frm.doc.name,
							refund_amount: values.refund_amount,
							reason: reason_values.refund_reason,
						},
						callback: function (response) {
							if (response.message.success) {
								frappe.show_alert({
									message: __("Refund created successfully"),
									indicator: "green",
								});
								frappe.set_route(
									"Form",
									"Payment Refund",
									response.message.refund
								);
							} else {
								frappe.msgprint({
									title: __("Refund Failed"),
									indicator: "red",
									message:
										response.message.message || __("Failed to create refund"),
								});
							}
						},
					});
				},
				__("Refund Reason"),
				__("Continue")
			);
		},
		__("Process Refund"),
		__("Create")
	);
}

function view_payment_link(frm) {
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Payment Link",
			filters: {
				payment_transaction: frm.doc.name,
			},
			fields: ["name", "payment_url"],
		},
		callback: function (response) {
			if (response.message && response.message.length > 0) {
				const payment_link = response.message[0];
				if (payment_link.payment_url) {
					window.open(payment_link.payment_url, "_blank");
				} else {
					frappe.msgprint(__("No payment URL found for this transaction"));
				}
			} else {
				frappe.msgprint(__("No payment link found for this transaction"));
			}
		},
	});
}

function retry_payment(frm) {
	frappe.confirm(__("Create a new payment request for this transaction?"), function () {
		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration.create_payment_request",
			args: {
				doctype: "Payment Transaction",
				docname: frm.doc.name,
				payment_method: frm.doc.payment_method,
			},
			callback: function (response) {
				if (response.message.success) {
					frappe.show_alert({
						message: __("New payment request created successfully"),
						indicator: "green",
					});
					if (response.message.payment_url) {
						window.open(response.message.payment_url, "_blank");
					}
				} else {
					frappe.msgprint({
						title: __("Retry Failed"),
						indicator: "red",
						message:
							response.message.message || __("Failed to create new payment request"),
					});
				}
			},
		});
	});
}

function create_payment_entry(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_transaction.payment_transaction.update_sales_invoice_payment",
		args: {
			transaction_name: frm.doc.name,
			invoice_name: frm.doc.reference_id, // This would need to be adjusted based on your reference structure
		},
		callback: function (response) {
			if (response.message && response.message.success) {
				frappe.show_alert({
					message: __("Payment Entry created successfully"),
					indicator: "green",
				});
			} else {
				frappe.msgprint({
					title: __("Payment Entry Creation Failed"),
					indicator: "red",
					message: response.message
						? response.message.message
						: __("Failed to create Payment Entry"),
				});
			}
		},
	});
}
