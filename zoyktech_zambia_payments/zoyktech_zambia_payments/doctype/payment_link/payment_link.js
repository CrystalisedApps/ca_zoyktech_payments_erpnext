frappe.ui.form.on("Payment Link", {
	refresh: function (frm) {
		// Add custom buttons
		add_custom_buttons(frm);

		// Show payment URL if available
		show_payment_url(frm);

		// Show status information
		show_status_info(frm);
	},

	validate: function (frm) {
		// Validate expiry date
		if (frm.doc.expiry_date) {
			const expiry_date = new Date(frm.doc.expiry_date);
			const now = new Date();

			if (expiry_date < now) {
				frappe.msgprint(__("Expiry date cannot be in the past"));
				frappe.validated = false;
			}
		}

		// Validate amount
		if (frm.doc.amount <= 0) {
			frappe.msgprint(__("Amount must be greater than 0"));
			frappe.validated = false;
		}
	},
});

function add_custom_buttons(frm) {
	// Add copy payment URL button
	if (frm.doc.payment_url) {
		frm.add_custom_button(__("Copy Payment URL"), function () {
			copy_to_clipboard(frm.doc.payment_url);
			frappe.show_alert({
				message: __("Payment URL copied to clipboard"),
				indicator: "green",
			});
		});
	}

	// Add send via email button
	frm.add_custom_button(__("Send via Email"), function () {
		send_payment_link_email(frm);
	});

	// Add send via SMS button
	if (frm.doc.customer_phone) {
		frm.add_custom_button(__("Send via SMS"), function () {
			send_payment_link_sms(frm);
		});
	}

	// Add cancel button for pending links
	if (frm.doc.status === "Pending") {
		frm.add_custom_button(
			__("Cancel Payment Link"),
			function () {
				cancel_payment_link(frm);
			},
			__("Actions")
		);
	}

	// Add view payment transaction button
	if (frm.doc.payment_transaction) {
		frm.add_custom_button(__("View Payment Transaction"), function () {
			frappe.set_route("Form", "Payment Transaction", frm.doc.payment_transaction);
		});
	}
}

function show_payment_url(frm) {
	if (frm.doc.payment_url) {
		const payment_url_html = `
            <div class="payment-url-section" style="margin: 15px 0;">
                <h5>${__("Payment URL")}</h5>
                <div class="input-group">
                    <input type="text" class="form-control" value="${
						frm.doc.payment_url
					}" readonly>
                    <div class="input-group-append">
                        <button class="btn btn-outline-secondary btn-copy-url" type="button">
                            <i class="fa fa-copy"></i>
                        </button>
                    </div>
                </div>
                <small class="text-muted">${__(
					"Share this URL with the customer to collect payment"
				)}</small>
            </div>
        `;

		frm.fields_dict.payment_url.$wrapper.html(payment_url_html);

		// Bind copy button
		frm.fields_dict.payment_url.$wrapper.find(".btn-copy-url").click(function () {
			copy_to_clipboard(frm.doc.payment_url);
			frappe.show_alert({
				message: __("Payment URL copied to clipboard"),
				indicator: "green",
			});
		});
	}
}

function show_status_info(frm) {
	let status_info = "";

	switch (frm.doc.status) {
		case "Pending":
			status_info = `
                <div class="alert alert-warning">
                    <h6>${__("Payment Pending")}</h6>
                    <p>${__("This payment link is active and waiting for payment.")}</p>
                    ${
						frm.doc.expiry_date
							? `<p><strong>${__("Expires:")}</strong> ${frappe.datetime.str_to_user(
									frm.doc.expiry_date
							  )}</p>`
							: ""
					}
                </div>
            `;
			break;

		case "Paid":
			status_info = `
                <div class="alert alert-success">
                    <h6>${__("Payment Completed")}</h6>
                    <p>${__("This payment has been successfully processed.")}</p>
                    ${
						frm.doc.payment_transaction
							? `<p><strong>${__("Transaction:")}</strong> ${
									frm.doc.payment_transaction
							  }</p>`
							: ""
					}
                </div>
            `;
			break;

		case "Failed":
			status_info = `
                <div class="alert alert-danger">
                    <h6>${__("Payment Failed")}</h6>
                    <p>${__("This payment attempt failed. You can create a new payment link.")}</p>
                </div>
            `;
			break;

		case "Cancelled":
			status_info = `
                <div class="alert alert-secondary">
                    <h6>${__("Payment Cancelled")}</h6>
                    <p>${__("This payment link has been cancelled.")}</p>
                </div>
            `;
			break;
	}

	if (status_info) {
		frm.dashboard.add_indicator(__("Payment Status"), status_info);
	}
}

function copy_to_clipboard(text) {
	const temp_input = document.createElement("input");
	temp_input.value = text;
	document.body.appendChild(temp_input);
	temp_input.select();
	document.execCommand("copy");
	document.body.removeChild(temp_input);
}

function send_payment_link_email(frm) {
	frappe.prompt(
		{
			fieldname: "email_address",
			label: __("Email Address"),
			fieldtype: "Data",
			reqd: 1,
			default: frm.doc.customer_email || "",
			description: __("Enter email address to send payment link"),
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_link.payment_link.send_payment_link_email",
				args: {
					payment_link: frm.doc.name,
					email_address: values.email_address,
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.show_alert({
							message: __("Payment link sent via email successfully"),
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
		__("Send Payment Link via Email"),
		__("Send")
	);
}

function send_payment_link_sms(frm) {
	frappe.prompt(
		{
			fieldname: "phone_number",
			label: __("Phone Number"),
			fieldtype: "Data",
			reqd: 1,
			default: frm.doc.customer_phone || "",
			description: __("Enter phone number to send payment link via SMS"),
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_link.payment_link.send_payment_link_sms",
				args: {
					payment_link: frm.doc.name,
					phone_number: values.phone_number,
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.show_alert({
							message: __("Payment link sent via SMS successfully"),
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
		__("Send Payment Link via SMS"),
		__("Send")
	);
}

function cancel_payment_link(frm) {
	frappe.confirm(
		__("Are you sure you want to cancel this payment link? This action cannot be undone."),
		function () {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_link.payment_link.cancel_payment_link",
				args: {
					reference_id: frm.doc.name,
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.show_alert({
							message: __("Payment link cancelled successfully"),
							indicator: "green",
						});
						frm.reload_doc();
					} else {
						frappe.msgprint({
							title: __("Cancellation Failed"),
							indicator: "red",
							message:
								response.message.message || __("Failed to cancel payment link"),
						});
					}
				},
			});
		}
	);
}
