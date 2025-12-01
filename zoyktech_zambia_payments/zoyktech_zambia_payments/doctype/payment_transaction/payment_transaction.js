frappe.ui.form.on("Payment Transaction", {
	refresh: function (frm) {
		// Add custom CSS first
		add_custom_css(frm);

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

function add_custom_css(frm) {
	// Add custom CSS to ensure styles are applied
	const customCSS = `
        .custom-gateway-response {
            margin: 15px 0;
            border: 1px solid #d1d8dd;
            border-radius: 4px;
            background-color: #fff;
        }
        
        .custom-gateway-response h5 {
            margin: 0;
            padding: 10px 15px;
            background-color: #f5f7fa;
            border-bottom: 1px solid #d1d8dd;
            font-weight: 600;
            font-size: 13px;
            color: #36414c;
        }
        
        .custom-gateway-response pre {
            margin: 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 0 0 4px 4px;
            max-height: 300px;
            overflow-y: auto;
            overflow-x: hidden;
            font-size: 12px;
            line-height: 1.4;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        
        .custom-status-indicator {
            margin-top: 15px;
        }
        
        .custom-status-indicator .alert {
            margin-bottom: 0;
            border-radius: 4px;
        }
        
        .custom-status-indicator h6 {
            margin-top: 0;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 13px;
        }
        
        .custom-status-indicator p {
            margin-bottom: 5px;
            font-size: 12px;
            line-height: 1.5;
        }
        
        .custom-status-indicator p:last-child {
            margin-bottom: 0;
        }
        
        .custom-status-indicator strong {
            color: #36414c;
        }
    `;

	// Check if CSS is already added to avoid duplicates
	if (!document.getElementById("custom-payment-css")) {
		const style = document.createElement("style");
		style.id = "custom-payment-css";
		style.textContent = customCSS;
		document.head.appendChild(style);
	}
}

function add_custom_buttons(frm) {
	// Clear existing custom buttons first
	frm.remove_custom_button(__("Check Status"));
	frm.remove_custom_button(__("Process Refund"));
	frm.remove_custom_button(__("View Payment Link"));
	frm.remove_custom_button(__("Retry Payment"));
	frm.remove_custom_button(__("Create Payment Entry"));

	// Add check status button for pending transactions
	if (frm.doc.status === "Pending") {
		frm.add_custom_button(
			__("Check Status"),
			function () {
				check_payment_status(frm);
			},
			__("Actions")
		);
	}

	// Add refund button for completed transactions
	if (frm.doc.status === "Completed" && !frm.doc.__islocal) {
		frm.add_custom_button(
			__("Process Refund"),
			function () {
				process_refund(frm);
			},
			__("Actions")
		);
	}

	// Add view payment link button
	if (frm.doc.reference_id && !frm.doc.__islocal) {
		frm.add_custom_button(
			__("View Payment Link"),
			function () {
				view_payment_link(frm);
			},
			__("Links")
		);
	}

	// Add retry button for failed transactions
	if (frm.doc.status === "Failed" && !frm.doc.__islocal) {
		frm.add_custom_button(
			__("Retry Payment"),
			function () {
				retry_payment(frm);
			},
			__("Actions")
		);
	}

	// Add create payment entry button
	if (frm.doc.status === "Completed" && !frm.doc.__islocal) {
		frm.add_custom_button(
			__("Create Payment Entry"),
			function () {
				create_payment_entry(frm);
			},
			__("Create")
		);
	}
}

function show_gateway_response(frm) {
	if (frm.doc.gateway_response && frm.fields_dict.gateway_response) {
		try {
			const response = JSON.parse(frm.doc.gateway_response);
			const formatted_response = JSON.stringify(response, null, 2);

			const response_html = `
                <div class="custom-gateway-response">
                    <h5>${__("Gateway Response")}</h5>
                    <pre>${frappe.utils.escape_html(formatted_response)}</pre>
                </div>
            `;

			// Check if we've already added our custom HTML
			const $wrapper = $(frm.fields_dict.gateway_response.$wrapper);
			if (!$wrapper.find(".custom-gateway-response").length) {
				$wrapper.html(response_html);
			}
		} catch (e) {
			// If not JSON, show as plain text
			const response_html = `
                <div class="custom-gateway-response">
                    <h5>${__("Gateway Response")}</h5>
                    <pre>${frappe.utils.escape_html(frm.doc.gateway_response)}</pre>
                </div>
            `;

			const $wrapper = $(frm.fields_dict.gateway_response.$wrapper);
			if (!$wrapper.find(".custom-gateway-response").length) {
				$wrapper.html(response_html);
			}
		}
	}
}

function show_status_info(frm) {
	if (!frm.doc.status) return;

	let status_info = "";
	let alert_class = "";

	switch (frm.doc.status) {
		case "Completed":
			alert_class = "alert-success";
			status_info = `
                <h6>${__("Payment Completed")}</h6>
                <p>${__(
					"This payment has been successfully processed and the funds have been received."
				)}</p>
                ${
					frm.doc.transaction_id
						? `<p><strong>${__("Transaction ID:")}</strong> ${frappe.utils.escape_html(
								frm.doc.transaction_id
						  )}</p>`
						: ""
				}
                ${
					frm.doc.modified
						? `<p><strong>${__("Completed:")}</strong> ${frappe.datetime.str_to_user(
								frm.doc.modified
						  )}</p>`
						: ""
				}
            `;
			break;

		case "Pending":
			alert_class = "alert-warning";
			status_info = `
                <h6>${__("Payment Pending")}</h6>
                <p>${__(
					"This payment is being processed. Please check back later for updates."
				)}</p>
                ${
					frm.doc.creation
						? `<p><strong>${__("Initiated:")}</strong> ${frappe.datetime.str_to_user(
								frm.doc.creation
						  )}</p>`
						: ""
				}
            `;
			break;

		case "Failed":
			alert_class = "alert-danger";
			status_info = `
                <h6>${__("Payment Failed")}</h6>
                <p>${__("This payment could not be processed.")}</p>
                ${
					frm.doc.failure_reason
						? `<p><strong>${__("Reason:")}</strong> ${frappe.utils.escape_html(
								frm.doc.failure_reason
						  )}</p>`
						: ""
				}
            `;
			break;

		case "Refunded":
			alert_class = "alert-info";
			status_info = `
                <h6>${__("Payment Refunded")}</h6>
                <p>${__("This payment has been refunded to the customer.")}</p>
                ${
					frm.doc.modified
						? `<p><strong>${__("Refunded:")}</strong> ${frappe.datetime.str_to_user(
								frm.doc.modified
						  )}</p>`
						: ""
				}
            `;
			break;

		default:
			alert_class = "alert-secondary";
			status_info = `
                <h6>${__("Payment Status")}: ${frm.doc.status}</h6>
                <p>${__("The payment is currently in this status.")}</p>
            `;
			break;
	}

	if (status_info) {
		// Clear any existing custom indicators
		frm.dashboard.clear_indicators();

		// Add the status indicator
		const indicator_html = `
            <div class="custom-status-indicator">
                <div class="alert ${alert_class}">
                    ${status_info}
                </div>
            </div>
        `;

		frm.dashboard.add_indicator(__("Payment Status"), indicator_html);
	}
}

function generate_reference_id(frm) {
	if (!frm.is_new()) return;

	const timestamp = new Date().getTime();
	const random = Math.random().toString(36).substring(2, 8).toUpperCase();
	frm.set_value("reference_id", `TXN_${timestamp}_${random}`);
}

function check_payment_status(frm) {
	if (!frm.doc.reference_id) {
		frappe.msgprint({
			title: __("Missing Reference"),
			indicator: "red",
			message: __("Reference ID is required to check payment status."),
		});
		return;
	}

	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.get_payment_status",
		args: {
			reference_id: frm.doc.reference_id,
		},
		freeze: true,
		freeze_message: __("Checking payment status..."),
		callback: function (response) {
			if (response.message && response.message.success) {
				const status = response.message.status;

				if (status !== frm.doc.status) {
					frappe.show_alert({
						message: __("Status updated from {0} to {1}", [frm.doc.status, status]),
						indicator: "green",
					});
					frm.reload_doc();
				} else {
					frappe.show_alert({
						message: __("Payment status is still {0}", [status]),
						indicator: "blue",
					});
				}
			} else {
				frappe.msgprint({
					title: __("Status Check Failed"),
					indicator: "red",
					message: response.message
						? response.message.message || __("Failed to check payment status")
						: __("Server request failed"),
				});
			}
		},
		error: function () {
			frappe.msgprint({
				title: __("Request Failed"),
				indicator: "red",
				message: __("Failed to connect to server. Please try again."),
			});
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
			max: frm.doc.amount,
			min: 0,
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
					options: [
						{ label: __("Customer Request"), value: "Customer Request" },
						{ label: __("Duplicate Payment"), value: "Duplicate Payment" },
						{ label: __("Service Not Provided"), value: "Service Not Provided" },
						{ label: __("Technical Error"), value: "Technical Error" },
						{ label: __("Fraudulent Transaction"), value: "Fraudulent Transaction" },
						{ label: __("Other"), value: "Other" },
					]
						.map((opt) => opt.label)
						.join("\n"),
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
						freeze: true,
						freeze_message: __("Creating refund..."),
						callback: function (response) {
							if (response.message && response.message.success) {
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
									message: response.message
										? response.message.message || __("Failed to create refund")
										: __("Server request failed"),
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
	if (!frm.doc.reference_id) {
		frappe.msgprint(__("No reference ID found for this transaction"));
		return;
	}

	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Payment Link",
			filters: [["payment_transaction", "=", frm.doc.name]],
			fields: ["name", "payment_url"],
			limit_page_length: 1,
		},
		callback: function (response) {
			if (response.message && response.message.length > 0) {
				const payment_link = response.message[0];
				if (payment_link.payment_url) {
					// Open in new tab
					window.open(payment_link.payment_url, "_blank").focus();
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
	frappe.confirm(
		__("Are you sure you want to create a new payment request for this transaction?"),
		function () {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration.create_payment_request",
				args: {
					doctype: "Payment Transaction",
					docname: frm.doc.name,
					payment_method: frm.doc.payment_method,
				},
				freeze: true,
				freeze_message: __("Creating payment request..."),
				callback: function (response) {
					if (response.message && response.message.success) {
						frappe.show_alert({
							message: __("New payment request created successfully"),
							indicator: "green",
						});
						if (response.message.payment_url) {
							window.open(response.message.payment_url, "_blank").focus();
						}
						// Reload to show updated status
						frm.reload_doc();
					} else {
						frappe.msgprint({
							title: __("Retry Failed"),
							indicator: "red",
							message: response.message
								? response.message.message ||
								  __("Failed to create new payment request")
								: __("Server request failed"),
						});
					}
				},
			});
		}
	);
}

function create_payment_entry(frm) {
	if (!frm.doc.reference_id) {
		frappe.msgprint({
			title: __("Missing Reference"),
			indicator: "red",
			message: __("Reference ID is required to create payment entry."),
		});
		return;
	}

	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_transaction.payment_transaction.update_sales_invoice_payment",
		args: {
			transaction_name: frm.doc.name,
			invoice_name: frm.doc.reference_id,
		},
		freeze: true,
		freeze_message: __("Creating payment entry..."),
		callback: function (response) {
			if (response.message && response.message.success) {
				frappe.show_alert({
					message: __("Payment Entry created successfully"),
					indicator: "green",
				});
				// Reload to show any updates
				frm.reload_doc();
			} else {
				frappe.msgprint({
					title: __("Payment Entry Creation Failed"),
					indicator: "red",
					message: response.message
						? response.message.message || __("Failed to create Payment Entry")
						: __("Server request failed"),
				});
			}
		},
	});
}

// Handle form refresh to reapply styles
$(document).on("form-refresh", function (e, frm) {
	if (frm && frm.doctype === "Payment Transaction") {
		// Small delay to ensure DOM is ready
		setTimeout(() => {
			add_custom_css(frm);
			show_gateway_response(frm);
		}, 100);
	}
});
