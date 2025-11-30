// Payment buttons and UI enhancements for various doctypes

// Sales Invoice Payment Integration
frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		addPaymentButtonsToSalesInvoice(frm);
		showPaymentStatus(frm);
	},
});

function addPaymentButtonsToSalesInvoice(frm) {
	if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0) {
		// Main payment button
		frm.add_custom_button(
			__("Create Payment Link"),
			function () {
				createPaymentLinkForSalesInvoice(frm);
			},
			__("Create")
		);

		// Quick payment buttons
		frm.add_custom_button(
			__("MTN Money"),
			function () {
				createQuickPayment(frm, "mtn");
			},
			__("Quick Pay")
		);

		frm.add_custom_button(
			__("Airtel Money"),
			function () {
				createQuickPayment(frm, "airtel");
			},
			__("Quick Pay")
		);

		frm.add_custom_button(
			__("Card Payment"),
			function () {
				createQuickPayment(frm, "card");
			},
			__("Quick Pay")
		);
	}
}

function createPaymentLinkForSalesInvoice(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Create Payment Link"),
		fields: [
			{
				fieldname: "payment_method",
				label: __("Payment Method"),
				fieldtype: "Select",
				options: "\nMTN Mobile Money\nAirtel Money\nCard Payment\nBank Transfer",
				default: "MTN Mobile Money",
			},
			{
				fieldname: "customer_phone",
				label: __("Customer Phone"),
				fieldtype: "Data",
				reqd: 1,
				default: frm.doc.contact_mobile || frm.doc.mobile_no,
				description: __("Customer will receive payment instructions via SMS"),
			},
			{
				fieldname: "customer_email",
				label: __("Customer Email"),
				fieldtype: "Data",
				default: frm.doc.contact_email,
				description: __("Payment receipt will be sent to this email"),
			},
			{
				fieldname: "amount",
				label: __("Amount"),
				fieldtype: "Currency",
				default: frm.doc.outstanding_amount,
				read_only: 1,
			},
			{
				fieldname: "expiry_days",
				label: __("Link Expires After (Days)"),
				fieldtype: "Int",
				default: 7,
				description: __("Payment link will expire after specified days"),
			},
			{
				fieldname: "send_sms",
				label: __("Send SMS Notification"),
				fieldtype: "Check",
				default: 1,
			},
			{
				fieldname: "send_email",
				label: __("Send Email Notification"),
				fieldtype: "Check",
				default: 1,
			},
		],
		primary_action_label: __("Create Payment Link"),
		primary_action: function (values) {
			dialog.hide();

			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration.create_payment_request",
				args: {
					doctype: "Sales Invoice",
					docname: frm.doc.name,
					payment_method: values.payment_method,
					customer_phone: values.customer_phone,
					customer_email: values.customer_email,
					expiry_days: values.expiry_days,
					send_sms: values.send_sms,
					send_email: values.send_email,
				},
				callback: function (response) {
					if (response.message.success) {
						showPaymentLinkSuccess(frm, response.message);
					} else {
						frappe.msgprint({
							title: __("Error"),
							indicator: "red",
							message:
								response.message.message || __("Failed to create payment link"),
						});
					}
				},
			});
		},
	});

	dialog.show();
}

function createQuickPayment(frm, method) {
	frappe.confirm(
		__("Create {0} payment link for {1} {2}?", [
			method.toUpperCase(),
			frm.doc.currency,
			frm.doc.outstanding_amount,
		]),
		function () {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration.create_payment_request",
				args: {
					doctype: "Sales Invoice",
					docname: frm.doc.name,
					payment_method: method,
				},
				callback: function (response) {
					if (response.message.success) {
						showQuickPaymentSuccess(frm, response.message, method);
					} else {
						frappe.msgprint({
							title: __("Error"),
							indicator: "red",
							message:
								response.message.message || __("Failed to create payment link"),
						});
					}
				},
			});
		}
	);
}

function showPaymentLinkSuccess(frm, result) {
	const dialog = new frappe.ui.Dialog({
		title: __("Payment Link Created"),
		fields: [
			{
				fieldname: "html_section",
				fieldtype: "HTML",
				options: `
                    <div class="payment-link-success">
                        <div class="alert alert-success">
                            <h5>${__("Payment Link Created Successfully!")}</h5>
                            <p>${__("Share this link with your customer to collect payment.")}</p>
                        </div>
                        
                        <div class="payment-link-info">
                            <div class="row">
                                <div class="col-sm-6">
                                    <strong>${__("Reference")}:</strong>
                                </div>
                                <div class="col-sm-6">
                                    ${result.reference_id}
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6">
                                    <strong>${__("Amount")}:</strong>
                                </div>
                                <div class="col-sm-6">
                                    ${result.payment_data.amount} ${result.payment_data.currency}
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-sm-6">
                                    <strong>${__("Payment URL")}:</strong>
                                </div>
                                <div class="col-sm-6">
                                    <a href="${result.payment_url}" target="_blank">${__(
					"Open Payment Page"
				)}</a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="payment-actions" style="margin-top: 20px;">
                            <button class="btn btn-primary btn-copy-url" style="margin-right: 10px;">
                                <i class="fa fa-copy"></i> ${__("Copy URL")}
                            </button>
                            <button class="btn btn-default btn-send-sms">
                                <i class="fa fa-mobile"></i> ${__("Send SMS")}
                            </button>
                            <button class="btn btn-default btn-send-email" style="margin-left: 10px;">
                                <i class="fa fa-envelope"></i> ${__("Send Email")}
                            </button>
                            <button class="btn btn-default btn-view-details" style="margin-left: 10px;">
                                <i class="fa fa-eye"></i> ${__("View Details")}
                            </button>
                        </div>
                        
                        <div class="qr-code-section" style="margin-top: 20px; text-align: center;">
                            <div id="paymentQrCode"></div>
                            <p class="text-muted small">${__("Scan QR Code to pay")}</p>
                        </div>
                    </div>
                `,
			},
		],
	});

	dialog.show();

	// Generate QR Code
	if (typeof QRCode !== "undefined" && result.payment_url) {
		new QRCode(document.getElementById("paymentQrCode"), {
			text: result.payment_url,
			width: 128,
			height: 128,
		});
	}

	// Bind button events
	dialog.fields_dict.html_section.$wrapper.find(".btn-copy-url").on("click", function () {
		copyToClipboard(result.payment_url);
		frappe.show_alert({ message: __("URL copied to clipboard"), indicator: "green" });
	});

	dialog.fields_dict.html_section.$wrapper.find(".btn-send-sms").on("click", function () {
		sendPaymentSMS(frm, result.reference_id);
	});

	dialog.fields_dict.html_section.$wrapper.find(".btn-send-email").on("click", function () {
		sendPaymentEmail(frm, result.reference_id);
	});

	dialog.fields_dict.html_section.$wrapper.find(".btn-view-details").on("click", function () {
		frappe.set_route("Form", "Payment Link", result.payment_link);
		dialog.hide();
	});
}

function showQuickPaymentSuccess(frm, result, method) {
	frappe.msgprint({
		title: __("Payment Link Created"),
		indicator: "green",
		message: __("{0} payment link created successfully. Reference: {1}", [
			method.toUpperCase(),
			result.reference_id,
		]),
	});

	// Open payment page in new tab
	if (result.payment_url) {
		window.open(result.payment_url, "_blank");
	}
}

function showPaymentStatus(frm) {
	// Check for existing payment links
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Payment Link",
			filters: {
				linked_doctype: "Sales Invoice",
				linked_docname: frm.doc.name,
			},
			fields: [
				"name",
				"status",
				"reference_id",
				"amount",
				"payment_method",
				"payment_url",
				"creation",
			],
			order_by: "creation desc",
		},
		callback: function (response) {
			if (response.message && response.message.length > 0) {
				updatePaymentStatusSection(frm, response.message);
			}
		},
	});
}

function updatePaymentStatusSection(frm, paymentLinks) {
	let statusHTML = `
        <div class="payment-links-status">
            <h5>${__("Active Payment Links")}</h5>
            <div class="payment-links-list">
    `;

	paymentLinks.forEach((link) => {
		const statusClass = getStatusBadgeClass(link.status);
		statusHTML += `
            <div class="payment-link-item" style="padding: 10px; border-bottom: 1px solid #e0e0e0;">
                <div class="row">
                    <div class="col-sm-3">
                        <strong>${link.reference_id}</strong>
                    </div>
                    <div class="col-sm-2">
                        <span class="badge ${statusClass}">${link.status}</span>
                    </div>
                    <div class="col-sm-2">
                        ${link.amount} ${frm.doc.currency}
                    </div>
                    <div class="col-sm-3">
                        ${link.payment_method || "N/A"}
                    </div>
                    <div class="col-sm-2">
                        ${
							link.payment_url
								? `<button class="btn btn-xs btn-default btn-copy-link" data-url="${
										link.payment_url
								  }">
                                ${__("Copy Link")}
                            </button>`
								: ""
						}
                    </div>
                </div>
            </div>
        `;
	});

	statusHTML += `
            </div>
        </div>
    `;

	// Update custom field
	frm.fields_dict.custom_payment_links.$wrapper.html(statusHTML);

	// Bind copy link events
	frm.fields_dict.custom_payment_links.$wrapper.find(".btn-copy-link").on("click", function () {
		const url = $(this).data("url");
		copyToClipboard(url);
		frappe.show_alert({ message: __("Payment link copied to clipboard"), indicator: "green" });
	});
}

function getStatusBadgeClass(status) {
	const classes = {
		Paid: "badge-success",
		Pending: "badge-warning",
		Failed: "badge-danger",
		Cancelled: "badge-secondary",
		Expired: "badge-secondary",
	};
	return classes[status] || "badge-secondary";
}

function copyToClipboard(text) {
	const tempInput = document.createElement("input");
	tempInput.value = text;
	document.body.appendChild(tempInput);
	tempInput.select();
	document.execCommand("copy");
	document.body.removeChild(tempInput);
}

function sendPaymentSMS(frm, referenceId) {
	frappe.prompt(
		{
			fieldname: "phone_number",
			label: __("Phone Number"),
			fieldtype: "Data",
			reqd: 1,
			description: __("Enter phone number to send SMS"),
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.send_payment_sms",
				args: {
					reference_id: referenceId,
					phone_number: values.phone_number,
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.show_alert({
							message: __("SMS sent successfully"),
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: __("SMS Failed"),
							indicator: "red",
							message: response.message.message || __("Failed to send SMS"),
						});
					}
				},
			});
		},
		__("Send Payment SMS"),
		__("Send")
	);
}

function sendPaymentEmail(frm, referenceId) {
	frappe.prompt(
		{
			fieldname: "email_address",
			label: __("Email Address"),
			fieldtype: "Data",
			fieldtype: "Data",
			reqd: 1,
			description: __("Enter email address to send payment link"),
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.send_payment_email",
				args: {
					reference_id: referenceId,
					email_address: values.email_address,
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.show_alert({
							message: __("Email sent successfully"),
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: __("Email Failed"),
							indicator: "red",
							message: response.message.message || __("Failed to send email"),
						});
					}
				},
			});
		},
		__("Send Payment Email"),
		__("Send")
	);
}

// Purchase Invoice Payment Integration
frappe.ui.form.on("Purchase Invoice", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0) {
			frm.add_custom_button(
				__("Make Payment"),
				function () {
					createPaymentForPurchaseInvoice(frm);
				},
				__("Payments")
			);
		}
	},
});

function createPaymentForPurchaseInvoice(frm) {
	frappe.confirm(
		__("Create payment for supplier {0}? Amount: {1} {2}", [
			frm.doc.supplier,
			frm.doc.outstanding_amount,
			frm.doc.currency,
		]),
		function () {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.payment_integration.create_payment_request",
				args: {
					doctype: "Purchase Invoice",
					docname: frm.doc.name,
					payment_method: "bank_transfer",
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.msgprint({
							title: __("Payment Initiated"),
							indicator: "green",
							message: __("Payment has been initiated. Reference: {0}", [
								response.message.reference_id,
							]),
						});
					} else {
						frappe.msgprint({
							title: __("Payment Failed"),
							indicator: "red",
							message: response.message.message || __("Failed to initiate payment"),
						});
					}
				},
			});
		}
	);
}

// Customer Payment History
frappe.ui.form.on("Customer", {
	refresh: function (frm) {
		showCustomerPaymentHistory(frm);
	},
});

function showCustomerPaymentHistory(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.helpers.get_customer_payment_history",
		args: {
			customer: frm.doc.name,
			limit: 10,
		},
		callback: function (response) {
			if (response.message && response.message.length > 0) {
				updateCustomerPaymentHistory(frm, response.message);
			}
		},
	});
}

function updateCustomerPaymentHistory(frm, payments) {
	let historyHTML = `
        <div class="customer-payment-history">
            <h5>${__("Recent Payments")}</h5>
            <div class="payment-history-list">
                <div class="row header-row" style="font-weight: bold; padding: 10px; border-bottom: 2px solid #e0e0e0;">
                    <div class="col-sm-3">${__("Date")}</div>
                    <div class="col-sm-3">${__("Reference")}</div>
                    <div class="col-sm-2">${__("Amount")}</div>
                    <div class="col-sm-2">${__("Method")}</div>
                    <div class="col-sm-2">${__("Status")}</div>
                </div>
    `;

	payments.forEach((payment) => {
		const statusClass = getStatusBadgeClass(payment.status);
		const date = payment.payment_completed
			? frappe.datetime.str_to_user(payment.payment_completed.split(" ")[0])
			: "-";

		historyHTML += `
            <div class="row payment-row" style="padding: 8px; border-bottom: 1px solid #f0f0f0;">
                <div class="col-sm-3">${date}</div>
                <div class="col-sm-3">
                    <a href="#Form/Payment Transaction/${payment.name}">${payment.reference_id}</a>
                </div>
                <div class="col-sm-2">${payment.amount} ${payment.currency}</div>
                <div class="col-sm-2">${payment.payment_method || "N/A"}</div>
                <div class="col-sm-2">
                    <span class="badge ${statusClass}">${payment.status}</span>
                </div>
            </div>
        `;
	});

	historyHTML += `
            </div>
        </div>
    `;

	frm.fields_dict.custom_payment_history.$wrapper.html(historyHTML);
}
