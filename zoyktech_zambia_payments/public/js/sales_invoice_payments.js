frappe.ui.form.on("Sales Invoice", {
	refresh: function (frm) {
		if (frm.doc.docstatus === 1 && frm.doc.outstanding_amount > 0) {
			// Add payment button to dashboard
			frm.add_custom_button(
				__("Create Payment Link"),
				function () {
					zoyktech_zambia_payments.createSalesInvoicePayment(frm);
				},
				__("Payments")
			);

			// Add payment button to form
			frm.add_custom_button(
				__("Request Payment"),
				function () {
					zoyktech_zambia_payments.createSalesInvoicePayment(frm);
				},
				__("Actions")
			);

			// Show payment status if exists
			zoyktech_zambia_payments.showPaymentStatus(frm);
		}

		// Add payment dashboard section
		zoyktech_zambia_payments.addPaymentDashboard(frm);
	},

	onload: function (frm) {
		// Add custom CSS for payment sections
		zoyktech_zambia_payments.addCustomCSS();
	},
});

// Sales Invoice specific payment functions
zoyktech_zambia_payments.createSalesInvoicePayment = function (frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Create Payment Link"),
		fields: [
			{
				fieldname: "payment_method",
				label: __("Payment Method"),
				fieldtype: "Select",
				options: "\nMobile Money\nCard\nBank Transfer",
				default: "Mobile Money",
			},
			{
				fieldname: "customer_phone",
				label: __("Customer Phone"),
				fieldtype: "Data",
				reqd: 1,
				description: __("Enter customer phone number for payment notifications"),
				default: frm.doc.contact_mobile || frm.doc.mobile_no,
			},
			{
				fieldname: "customer_email",
				label: __("Customer Email"),
				fieldtype: "Data",
				default: frm.doc.contact_email || frm.doc.customer_email,
				description: __("Enter customer email for payment receipt"),
			},
			{
				fieldname: "amount",
				label: __("Amount"),
				fieldtype: "Currency",
				default: frm.doc.outstanding_amount,
				read_only: 1,
			},
			{
				fieldname: "expiry_hours",
				label: __("Link Expiry (Hours)"),
				fieldtype: "Int",
				default: 24,
				description: __("Payment link will expire after specified hours"),
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
					expiry_hours: values.expiry_hours,
				},
				callback: function (response) {
					if (response.message.success) {
						zoyktech_zambia_payments.showPaymentLinkDialog(frm, response.message);
					} else {
						frappe.msgprint({
							title: __("Payment Error"),
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
};

zoyktech_zambia_payments.showPaymentLinkDialog = function (frm, result) {
	const dialog = new frappe.ui.Dialog({
		title: __("Payment Link Created"),
		fields: [
			{
				fieldname: "payment_url",
				label: __("Payment URL"),
				fieldtype: "Data",
				read_only: 1,
				default: result.payment_url,
			},
			{
				fieldname: "reference_id",
				label: __("Reference ID"),
				fieldtype: "Data",
				read_only: 1,
				default: result.reference_id,
			},
			{
				fieldname: "html_section",
				fieldtype: "HTML",
				options: `
                    <div class="payment-link-actions">
                        <button class="btn btn-primary btn-copy-url" style="margin-right: 10px;">
                            ${__("Copy URL")}
                        </button>
                        <button class="btn btn-default btn-send-sms">
                            ${__("Send SMS")}
                        </button>
                        <button class="btn btn-default btn-send-email" style="margin-left: 10px;">
                            ${__("Send Email")}
                        </button>
                    </div>
                    <div class="payment-qr-code" style="margin-top: 20px; text-align: center;">
                        <div id="qrcode"></div>
                        <p class="text-muted small">${__("Scan to pay")}</p>
                    </div>
                `,
			},
		],
	});

	dialog.show();

	// Add copy URL functionality
	dialog.fields_dict.html_section.$wrapper.find(".btn-copy-url").on("click", function () {
		const urlField = dialog.fields_dict.payment_url.$input[0];
		urlField.select();
		document.execCommand("copy");
		frappe.show_alert({ message: __("URL copied to clipboard"), indicator: "green" });
	});

	// Generate QR code
	if (typeof QRCode !== "undefined" && result.payment_url) {
		new QRCode(document.getElementById("qrcode"), {
			text: result.payment_url,
			width: 128,
			height: 128,
		});
	}
};

zoyktech_zambia_payments.showPaymentStatus = function (frm) {
	// Check for existing payment links
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Payment Link",
			filters: {
				linked_doctype: "Sales Invoice",
				linked_docname: frm.doc.name,
			},
			fields: ["name", "status", "reference_id", "amount", "payment_url", "creation"],
		},
		callback: function (response) {
			if (response.message && response.message.length > 0) {
				const paymentLinks = response.message;

				let statusHTML = `
                    <div class="payment-status-section">
                        <h5>${__("Payment Links")}</h5>
                        <div class="payment-links-list">
                `;

				paymentLinks.forEach((link) => {
					const statusClass = zoyktech_zambia_payments.getStatusClass(link.status);
					statusHTML += `
                        <div class="payment-link-item">
                            <div class="row">
                                <div class="col-sm-4">
                                    <strong>${__("Reference")}:</strong> ${link.reference_id}
                                </div>
                                <div class="col-sm-2">
                                    <span class="badge ${statusClass}">${link.status}</span>
                                </div>
                                <div class="col-sm-3">
                                    <strong>${__("Amount")}:</strong> ${link.amount}
                                </div>
                                <div class="col-sm-3">
                                    <button class="btn btn-xs btn-default btn-copy-link" 
                                            data-url="${link.payment_url}">
                                        ${__("Copy Link")}
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
				});

				statusHTML += `
                        </div>
                    </div>
                `;

				// Add to form dashboard
				frm.dashboard.add_section(statusHTML, __("Payment Links"));

				// Bind copy link events
				frm.dashboard.$wrapper.find(".btn-copy-link").on("click", function () {
					const url = $(this).data("url");
					const tempInput = document.createElement("input");
					tempInput.value = url;
					document.body.appendChild(tempInput);
					tempInput.select();
					document.execCommand("copy");
					document.body.removeChild(tempInput);
					frappe.show_alert({
						message: __("Link copied to clipboard"),
						indicator: "green",
					});
				});
			}
		},
	});
};

zoyktech_zambia_payments.addPaymentDashboard = function (frm) {
	const dashboardHTML = `
        <div class="payment-dashboard">
            <div class="row">
                <div class="col-sm-4">
                    <div class="payment-stat-card">
                        <h6>${__("Outstanding Amount")}</h6>
                        <h3>${zoyktech_zambia_payments.format_currency(
							frm.doc.outstanding_amount,
							frm.doc.currency
						)}</h3>
                    </div>
                </div>
                <div class="col-sm-4">
                    <div class="payment-stat-card">
                        <h6>${__("Paid Amount")}</h6>
                        <h3>${zoyktech_zambia_payments.format_currency(
							frm.doc.paid_amount,
							frm.doc.currency
						)}</h3>
                    </div>
                </div>
                <div class="col-sm-4">
                    <div class="payment-stat-card">
                        <h6>${__("Grand Total")}</h6>
                        <h3>${zoyktech_zambia_payments.format_currency(
							frm.doc.grand_total,
							frm.doc.currency
						)}</h3>
                    </div>
                </div>
            </div>
        </div>
    `;

	frm.dashboard.add_section(dashboardHTML, __("Payment Overview"));
};

zoyktech_zambia_payments.getStatusClass = function (status) {
	const statusClasses = {
		Paid: "badge-success",
		Pending: "badge-warning",
		Failed: "badge-danger",
		Cancelled: "badge-secondary",
	};
	return statusClasses[status] || "badge-secondary";
};

zoyktech_zambia_payments.addCustomCSS = function () {
	const css = `
        .payment-status-section {
            margin: 15px 0;
        }
        .payment-link-item {
            padding: 10px;
            border-bottom: 1px solid #e0e0e0;
        }
        .payment-link-item:last-child {
            border-bottom: none;
        }
        .payment-stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .payment-stat-card h6 {
            margin-bottom: 5px;
            color: #6c757d;
        }
        .payment-stat-card h3 {
            margin: 0;
            color: #495057;
        }
        .payment-methods-dropdown {
            margin-left: 10px;
        }
    `;

	if (!$("#zoyktech-zambia-payments-css").length) {
		$('<style id="zoyktech-zambia-payments-css">' + css + "</style>").appendTo("head");
	}
};
