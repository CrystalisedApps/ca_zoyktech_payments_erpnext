frappe.provide("zoyktech_zambia_payments");

zoyktech_zambia_payments.PaymentIntegration = class {
	constructor() {
		this.init();
	}

	init() {
		this.bind_events();
		this.setup_realtime_updates();
	}

	bind_events() {
		// Use document ready to ensure DOM is loaded
		$(document).ready(() => {
			$(document).on("click", ".btn-create-payment", this.create_payment.bind(this));
			$(document).on(
				"click",
				".btn-check-payment-status",
				this.check_payment_status.bind(this)
			);
			$(document).on("click", ".btn-cancel-payment", this.cancel_payment.bind(this));
			// Bind dropdown items
			$(document).on(
				"click",
				".payment-methods-dropdown .dropdown-item",
				this.handle_payment_method_select.bind(this)
			);
		});
	}

	setup_realtime_updates() {
		// Wait for frappe to be ready
		if (typeof frappe !== "undefined" && frappe.realtime) {
			// Listen for payment status updates
			frappe.realtime.on("payment_completed", (data) => {
				this.handle_payment_completed(data);
			});

			frappe.realtime.on("payment_failed", (data) => {
				this.handle_payment_failed(data);
			});

			frappe.realtime.on("payment_pending", (data) => {
				this.handle_payment_pending(data);
			});
		} else {
			// Try again in 1 second
			setTimeout(() => this.setup_realtime_updates(), 1000);
		}
	}

	create_payment(event) {
		event.preventDefault();
		const $btn = $(event.currentTarget);
		const doctype = $btn.data("doctype");
		const docname = $btn.data("docname");
		const payment_method = $btn.data("payment-method");

		if (!doctype || !docname) {
			frappe.msgprint(__("Missing required data for payment creation"));
			return;
		}

		$btn.prop("disabled", true).html(__("Creating Payment..."));

		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.create_payment",
			args: {
				doctype: doctype,
				docname: docname,
				payment_method: payment_method || null,
			},
			callback: (response) => {
				$btn.prop("disabled", false).html(__("Create Payment"));

				if (response.message && response.message.success) {
					this.handle_payment_created(response.message);
				} else {
					frappe.msgprint({
						title: __("Payment Error"),
						indicator: "red",
						message:
							(response.message && response.message.message) ||
							__("Failed to create payment"),
					});
				}
			},
			error: () => {
				$btn.prop("disabled", false).html(__("Create Payment"));
				frappe.msgprint(__("Error creating payment"));
			},
		});
	}

	handle_payment_method_select(event) {
		event.preventDefault();
		const $item = $(event.currentTarget);
		const payment_method = $item.data("payment-method");
		const doctype = $item.data("doctype");
		const docname = $item.data("docname");

		// Find the associated payment button
		const $container = $item.closest(".payment-button-container");
		const $paymentBtn = $container.find(".btn-create-payment");

		// Update button with selected payment method
		$paymentBtn.data("payment-method", payment_method);

		// Update button text to show selected method
		const currentText = $paymentBtn.text().split(" - ")[0];
		$paymentBtn.text(`${currentText} - ${$item.text().trim()}`);

		// Trigger payment creation
		$paymentBtn.click();
	}

	handle_payment_created(result) {
		if (result.payment_url) {
			// Open payment page in new window
			window.open(result.payment_url, "_blank");

			frappe.msgprint({
				title: __("Payment Created"),
				indicator: "green",
				message: __(
					"Payment link has been created. You will be redirected to the payment page."
				),
			});

			// Start polling for payment status
			if (result.reference_id) {
				this.start_payment_polling(result.reference_id);
			}
		} else {
			frappe.msgprint({
				title: __("Payment Created"),
				indicator: "green",
				message: __("Payment request created successfully. Reference: {0}", [
					result.reference_id || "N/A",
				]),
			});
		}
	}

	start_payment_polling(reference_id) {
		const pollInterval = setInterval(() => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.get_payment_status",
				args: {
					reference_id: reference_id,
				},
				callback: (response) => {
					if (response.message && response.message.success) {
						const status = response.message.status;

						if (status === "Completed") {
							clearInterval(pollInterval);
							this.handle_payment_completed({
								reference: reference_id,
								status: status,
							});
						} else if (status === "Failed") {
							clearInterval(pollInterval);
							this.handle_payment_failed({
								reference: reference_id,
								status: status,
							});
						}
						// Continue polling for other statuses
					}
				},
			});
		}, 5000); // Poll every 5 seconds

		// Stop polling after 10 minutes
		setTimeout(() => {
			clearInterval(pollInterval);
		}, 600000);
	}

	check_payment_status(event) {
		event.preventDefault();
		const $btn = $(event.currentTarget);
		const reference_id = $btn.data("reference-id");

		if (!reference_id) {
			frappe.msgprint(__("No payment reference provided"));
			return;
		}

		$btn.prop("disabled", true).html(__("Checking..."));

		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.get_payment_status",
			args: {
				reference_id: reference_id,
			},
			callback: (response) => {
				$btn.prop("disabled", false).html(__("Check Status"));

				if (response.message && response.message.success) {
					const status = response.message.status;
					let indicator = "blue";
					let message = __("Payment status: {0}", [status]);

					if (status === "Completed") {
						indicator = "green";
						message = __("Payment completed successfully");
					} else if (status === "Failed") {
						indicator = "red";
						message = __("Payment failed");
					} else if (status === "Pending") {
						indicator = "orange";
						message = __("Payment is pending");
					}

					frappe.msgprint({
						title: __("Payment Status"),
						indicator: indicator,
						message: message,
					});
				} else {
					frappe.msgprint({
						title: __("Status Check Failed"),
						indicator: "red",
						message:
							(response.message && response.message.message) ||
							__("Failed to check payment status"),
					});
				}
			},
		});
	}

	cancel_payment(event) {
		event.preventDefault();
		const $btn = $(event.currentTarget);
		const reference_id = $btn.data("reference-id");

		if (!reference_id) {
			frappe.msgprint(__("No payment reference provided"));
			return;
		}

		frappe.confirm(__("Are you sure you want to cancel this payment request?"), () => {
			$btn.prop("disabled", true).html(__("Cancelling..."));

			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.cancel_payment",
				args: {
					reference_id: reference_id,
				},
				callback: (response) => {
					$btn.prop("disabled", false).html(__("Cancel Payment"));

					if (response.message && response.message.success) {
						frappe.msgprint({
							title: __("Payment Cancelled"),
							indicator: "orange",
							message: __("Payment request has been cancelled successfully"),
						});

						// Refresh the page or update UI
						if (cur_frm) {
							cur_frm.reload_doc();
						}
					} else {
						frappe.msgprint({
							title: __("Cancellation Failed"),
							indicator: "red",
							message:
								(response.message && response.message.message) ||
								__("Failed to cancel payment"),
						});
					}
				},
			});
		});
	}

	handle_payment_completed(data) {
		frappe.show_alert({
			message: __("Payment completed successfully for reference: {0}", [data.reference]),
			indicator: "green",
		});

		// Refresh current form if applicable
		if (cur_frm) {
			cur_frm.reload_doc();
		}

		// Update any payment status indicators on the page
		this.update_payment_status_indicators(data.reference, "Completed");
	}

	handle_payment_failed(data) {
		frappe.show_alert({
			message: __("Payment failed for reference: {0}", [data.reference]),
			indicator: "red",
		});

		this.update_payment_status_indicators(data.reference, "Failed");
	}

	handle_payment_pending(data) {
		this.update_payment_status_indicators(data.reference, "Pending");
	}

	update_payment_status_indicators(reference_id, status) {
		// Find and update all elements with this reference
		$(`[data-reference-id="${reference_id}"]`).each((index, element) => {
			const $element = $(element);
			const $statusBadge = $element.find(".payment-status");

			if ($statusBadge.length) {
				$statusBadge
					.removeClass(
						"badge-success badge-danger badge-warning badge-info badge-secondary"
					)
					.addClass(this.get_status_badge_class(status))
					.text(status);
			}
		});
	}

	get_status_badge_class(status) {
		const statusClasses = {
			Completed: "badge-success",
			Failed: "badge-danger",
			Pending: "badge-warning",
			Cancelled: "badge-secondary",
			Refunded: "badge-info",
		};
		return statusClasses[status] || "badge-secondary";
	}

	// Method to create payment button dynamically
	create_payment_button(doctype, docname, amount, currency, payment_methods = []) {
		const buttonHtml = `
            <div class="payment-button-container">
                ${this.create_payment_methods_dropdown(payment_methods, doctype, docname)}
                <button class="btn btn-primary btn-create-payment" 
                        data-doctype="${doctype}" 
                        data-docname="${docname}">
                    ${__("Pay")} ${amount} ${currency}
                </button>
            </div>
        `;
		return buttonHtml;
	}

	create_payment_methods_dropdown(payment_methods, doctype, docname) {
		if (!payment_methods || payment_methods.length === 0) {
			return "";
		}

		const dropdownItems = payment_methods
			.map(
				(method) => `
                    <a class="dropdown-item" href="#" 
                       data-payment-method="${method.value}"
                       data-doctype="${doctype}"
                       data-docname="${docname}">
                        ${method.label}
                    </a>
                `
			)
			.join("");

		return `
            <div class="dropdown payment-methods-dropdown" style="display: inline-block;">
                <button class="btn btn-secondary dropdown-toggle" type="button" 
                        data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                    ${__("Select Method")}
                </button>
                <div class="dropdown-menu">
                    ${dropdownItems}
                </div>
            </div>
        `;
	}

	// Add payment status badge to element
	add_payment_status_badge(reference_id, status, parent_selector) {
		const badgeClass = this.get_status_badge_class(status);
		const badgeHtml = `
            <span class="badge ${badgeClass} payment-status" data-reference-id="${reference_id}">
                ${status}
            </span>
        `;
		$(parent_selector).append(badgeHtml);
	}

	// Add payment action buttons
	add_payment_actions(reference_id, parent_selector, show_cancel = true) {
		const actionsHtml = `
            <div class="payment-actions" data-reference-id="${reference_id}">
                <button class="btn btn-sm btn-secondary btn-check-payment-status" 
                        data-reference-id="${reference_id}">
                    ${__("Check Status")}
                </button>
                ${
					show_cancel
						? `
                    <button class="btn btn-sm btn-danger btn-cancel-payment" 
                            data-reference-id="${reference_id}">
                        ${__("Cancel")}
                    </button>
                `
						: ""
				}
            </div>
        `;
		$(parent_selector).append(actionsHtml);
	}
};

// Initialize payment integration when DOM is ready
$(document).ready(function () {
	window.zoyktechZambiaPayments = new zoyktech_zambia_payments.PaymentIntegration();
});

// Utility functions
zoyktech_zambia_payments.format_currency = function (amount, currency = "ZMW") {
	try {
		return new Intl.NumberFormat("en-ZM", {
			style: "currency",
			currency: currency,
		}).format(amount);
	} catch (e) {
		return `${currency} ${parseFloat(amount).toFixed(2)}`;
	}
};

zoyktech_zambia_payments.validate_phone = function (phone) {
	if (!phone) return false;
	const zmPhoneRegex = /^(\+260|260|0)(76|77|96|97)\d{7}$/;
	return zmPhoneRegex.test(phone.replace(/\s/g, ""));
};

// Make it available globally immediately
if (typeof window !== "undefined") {
	window.zoyktech_zambia_payments = zoyktech_zambia_payments;
}
