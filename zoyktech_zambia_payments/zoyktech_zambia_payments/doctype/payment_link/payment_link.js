// payment_link.js

// =============================================
// FORM VIEW SCRIPT - Payment Link
// =============================================

frappe.ui.form.on("Payment Link", {
	refresh: function (frm) {
		// Add custom CSS first
		add_custom_css(frm);

		// Add custom buttons
		add_custom_buttons(frm);

		// Show payment URL if available
		show_payment_url(frm);

		// Show status information
		show_status_info(frm);

		// Show QR Code for payment URL
		show_qr_code(frm);

		// Show usage statistics
		show_usage_stats(frm);
	},

	validate: function (frm) {
		// Validate expiry date
		if (frm.doc.expiry_date) {
			const expiry_date = new Date(frm.doc.expiry_date);
			const now = new Date();

			if (expiry_date < now) {
				frappe.throw(__("Expiry date cannot be in the past"));
			}
		}

		// Validate amount
		if (frm.doc.amount <= 0) {
			frappe.throw(__("Amount must be greater than 0"));
		}

		// Validate customer email format
		if (frm.doc.customer_email && !isValidEmail(frm.doc.customer_email)) {
			frappe.throw(__("Please enter a valid email address"));
		}

		// Validate phone number format
		if (frm.doc.customer_phone && !isValidPhone(frm.doc.customer_phone)) {
			frappe.throw(__("Please enter a valid phone number"));
		}
	},

	amount: function (frm) {
		// Update payment URL if amount changes
		if (frm.doc.payment_url) {
			setTimeout(() => {
				show_payment_url(frm);
			}, 500);
		}
	},

	expiry_date: function (frm) {
		// Show warning if expiry date is soon
		if (frm.doc.expiry_date) {
			const expiry_date = new Date(frm.doc.expiry_date);
			const now = new Date();
			const days_until_expiry = Math.ceil((expiry_date - now) / (1000 * 60 * 60 * 24));

			if (days_until_expiry <= 1) {
				frappe.show_alert({
					message: __("Payment link expires in {0} day(s)", [days_until_expiry]),
					indicator: "orange",
				});
			}
		}
	},
});

function add_custom_css(frm) {
	// Add custom CSS to ensure styles are applied
	const customCSS = `
        .custom-payment-url-section {
            margin: 20px 0;
            border: 1px solid #d1d8dd;
            border-radius: 6px;
            background-color: #fff;
            overflow: hidden;
        }

        .custom-payment-url-section h5 {
            margin: 0;
            padding: 12px 15px;
            background-color: #f5f7fa;
            border-bottom: 1px solid #d1d8dd;
            font-weight: 600;
            font-size: 14px;
            color: #36414c;
        }

        .custom-payment-url-section .input-group {
            border-radius: 0;
            margin: 0;
        }

        .custom-payment-url-section .form-control {
            border: none;
            border-radius: 0;
            padding: 15px;
            font-size: 13px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            background-color: #f8f9fa;
        }

        .custom-payment-url-section .btn-copy-url {
            border: none;
            background-color: #5e64ff;
            color: white;
            padding: 0 20px;
            border-radius: 0;
            transition: background-color 0.2s ease;
        }

        .custom-payment-url-section .btn-copy-url:hover {
            background-color: #4a50e0;
        }

        .custom-payment-url-section small {
            display: block;
            padding: 10px 15px;
            background-color: #f5f7fa;
            border-top: 1px solid #d1d8dd;
            font-size: 12px;
            color: #6c7680;
        }

        .custom-status-indicator {
            margin-top: 20px;
        }

        .custom-status-indicator .alert {
            margin-bottom: 0;
            border-radius: 6px;
            border: 1px solid;
        }

        .custom-status-indicator h6 {
            margin-top: 0;
            margin-bottom: 10px;
            font-weight: 600;
            font-size: 14px;
        }

        .custom-status-indicator p {
            margin-bottom: 8px;
            font-size: 13px;
            line-height: 1.5;
        }

        .custom-status-indicator p:last-child {
            margin-bottom: 0;
        }

        .custom-status-indicator strong {
            color: #36414c;
            font-weight: 600;
        }

        .qr-code-container {
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #d1d8dd;
        }

        .qr-code-container h6 {
            margin-top: 0;
            margin-bottom: 15px;
            font-weight: 600;
            color: #36414c;
        }

        .qr-code-img {
            max-width: 200px;
            margin: 0 auto;
        }

        .usage-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }

        .stat-card {
            background: white;
            border: 1px solid #d1d8dd;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .stat-card .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #5e64ff;
            margin-bottom: 5px;
        }

        .stat-card .stat-label {
            font-size: 12px;
            color: #6c7680;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-card.success {
            border-left: 4px solid #5cb85c;
        }

        .stat-card.warning {
            border-left: 4px solid #f0ad4e;
        }

        .stat-card.info {
            border-left: 4px solid #5bc0de;
        }

        .custom-buttons-section {
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #d1d8dd;
        }

        .custom-buttons-section h6 {
            margin-top: 0;
            margin-bottom: 15px;
            font-weight: 600;
            color: #36414c;
        }

        .button-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
    `;

	// Check if CSS is already added to avoid duplicates
	if (!document.getElementById("custom-payment-link-css")) {
		const style = document.createElement("style");
		style.id = "custom-payment-link-css";
		style.textContent = customCSS;
		document.head.appendChild(style);
	}
}

function add_custom_buttons(frm) {
	// Clear existing custom buttons first
	frm.remove_custom_button(__("Copy Payment URL"));
	frm.remove_custom_button(__("Send via Email"));
	frm.remove_custom_button(__("Send via SMS"));
	frm.remove_custom_button(__("Cancel Payment Link"));
	frm.remove_custom_button(__("View Payment Transaction"));
	frm.remove_custom_button(__("Generate QR Code"));
	frm.remove_custom_button(__("View Analytics"));

	// Add copy payment URL button
	if (frm.doc.payment_url && frm.doc.status === "Pending") {
		frm.add_custom_button(
			__("Copy Payment URL"),
			function () {
				copy_to_clipboard(frm.doc.payment_url);
				frappe.show_alert({
					message: __("Payment URL copied to clipboard"),
					indicator: "green",
				});
			},
			__("Share")
		);
	}

	// Add send via email button
	if (frm.doc.status === "Pending") {
		frm.add_custom_button(
			__("Send via Email"),
			function () {
				send_payment_link_email(frm);
			},
			__("Share")
		);
	}

	// Add send via SMS button
	if (frm.doc.customer_phone && frm.doc.status === "Pending") {
		frm.add_custom_button(
			__("Send via SMS"),
			function () {
				send_payment_link_sms(frm);
			},
			__("Share")
		);
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
		frm.add_custom_button(
			__("View Payment"),
			function () {
				frappe.set_route("Form", "Payment Transaction", frm.doc.payment_transaction);
			},
			__("Related")
		);
	}

	// Add regenerate link button for expired/cancelled links
	if (["Expired", "Cancelled", "Failed"].includes(frm.doc.status)) {
		frm.add_custom_button(
			__("Create New Link"),
			function () {
				create_new_payment_link(frm);
			},
			__("Actions")
		);
	}

	// Add duplicate button
	if (!frm.doc.__islocal) {
		frm.add_custom_button(
			__("Duplicate"),
			function () {
				duplicate_payment_link(frm);
			},
			__("Create")
		);
	}
}

function show_payment_url(frm) {
	if (frm.doc.payment_url && frm.fields_dict.payment_url) {
		const is_expired = frm.doc.expiry_date && new Date(frm.doc.expiry_date) < new Date();
		const is_active = frm.doc.status === "Pending" && !is_expired;

		const payment_url_html = `
            <div class="custom-payment-url-section">
                <h5>${__("Payment URL")}</h5>
                <div class="input-group">
                    <input type="text" class="form-control" value="${frappe.utils.escape_html(
						frm.doc.payment_url
					)}" readonly
                        style="${!is_active ? "background-color: #f8f9fa; color: #8d99a6;" : ""}">
                    <div class="input-group-append">
                        <button class="btn btn-copy-url" type="button"
                            ${!is_active ? 'disabled style="background-color: #8d99a6;"' : ""}>
                            <i class="fa fa-copy"></i> ${__("Copy")}
                        </button>
                    </div>
                </div>
                <small class="text-muted">
                    ${
						is_active
							? __("Share this URL with the customer to collect payment")
							: __("This payment link is no longer active")
					}
                    ${
						frm.doc.expiry_date
							? `<br>${__("Expires:")} ${frappe.datetime.str_to_user(
									frm.doc.expiry_date
							  )}`
							: ""
					}
                </small>
            </div>
        `;

		const $wrapper = $(frm.fields_dict.payment_url.$wrapper);
		if (!$wrapper.find(".custom-payment-url-section").length) {
			$wrapper.html(payment_url_html);
		} else {
			$wrapper.find(".custom-payment-url-section").replaceWith(payment_url_html);
		}

		// Bind copy button
		if (is_active) {
			frm.fields_dict.payment_url.$wrapper
				.find(".btn-copy-url")
				.off("click")
				.click(function () {
					copy_to_clipboard(frm.doc.payment_url);
					frappe.show_alert({
						message: __("Payment URL copied to clipboard"),
						indicator: "green",
					});
				});
		}
	}
}

function show_status_info(frm) {
	if (!frm.doc.status) return;

	let status_info = "";
	let alert_class = "";

	switch (frm.doc.status) {
		case "Pending":
			alert_class = "alert-warning";
			const is_expired = frm.doc.expiry_date && new Date(frm.doc.expiry_date) < new Date();

			if (is_expired) {
				status_info = `
                    <h6>${__("Payment Link Expired")}</h6>
                    <p>${__("This payment link has expired. You can create a new one.")}</p>
                `;
				alert_class = "alert-secondary";
			} else {
				status_info = `
                    <h6>${__("Payment Pending")}</h6>
                    <p>${__("This payment link is active and waiting for payment.")}</p>
                    ${
						frm.doc.expiry_date
							? `<p><strong>${__("Expires:")}</strong> ${frappe.datetime.str_to_user(
									frm.doc.expiry_date
							  )}</p>`
							: ""
					}
                `;
			}
			break;

		case "Paid":
			alert_class = "alert-success";
			status_info = `
                <h6>${__("Payment Completed")}</h6>
                <p>${__("This payment has been successfully processed.")}</p>
                ${
					frm.doc.payment_transaction
						? `<p><strong>${__("Transaction:")}</strong> ${
								frm.doc.payment_transaction
						  }</p>`
						: ""
				}
                ${
					frm.doc.modified
						? `<p><strong>${__("Paid on:")}</strong> ${frappe.datetime.str_to_user(
								frm.doc.modified
						  )}</p>`
						: ""
				}
            `;
			break;

		case "Failed":
			alert_class = "alert-danger";
			status_info = `
                <h6>${__("Payment Failed")}</h6>
                <p>${__("This payment attempt failed. You can create a new payment link.")}</p>
            `;
			break;

		case "Cancelled":
			alert_class = "alert-secondary";
			status_info = `
                <h6>${__("Payment Cancelled")}</h6>
                <p>${__("This payment link has been cancelled.")}</p>
            `;
			break;

		case "Expired":
			alert_class = "alert-secondary";
			status_info = `
                <h6>${__("Payment Link Expired")}</h6>
                <p>${__("This payment link has expired. You can create a new one.")}</p>
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

function show_qr_code(frm) {
	if (frm.doc.payment_url && frm.doc.status === "Pending") {
		// Check if QR code already exists
		if ($(".qr-code-container").length) return;

		const qr_code_html = `
            <div class="qr-code-container">
                <h6>${__("Scan to Pay")}</h6>
                <div class="qr-code-img">
                    <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(
						frm.doc.payment_url
					)}"
                         alt="Payment QR Code"
                         style="width: 100%; height: auto; border-radius: 4px;">
                </div>
                <p style="margin-top: 10px; font-size: 12px; color: #6c7680;">
                    ${__("Scan this QR code with your mobile payment app")}
                </p>
            </div>
        `;

		// Insert QR code after payment URL field
		const $payment_url_wrapper = $(frm.fields_dict.payment_url.$wrapper);
		if ($payment_url_wrapper.length) {
			$payment_url_wrapper.after(qr_code_html);
		}
	}
}

function show_usage_stats(frm) {
	if (frm.doc.__islocal) return;

	frappe.call({
		method: "frappe.client.get_count",
		args: {
			doctype: "Payment Transaction",
			filters: {
				payment_link: frm.doc.name,
			},
		},
		callback: function (response) {
			const transaction_count = response.message || 0;

			const stats_html = `
                <div class="usage-stats">
                    <div class="stat-card success">
                        <div class="stat-value">${transaction_count}</div>
                        <div class="stat-label">${__("Transactions")}</div>
                    </div>
                    <div class="stat-card ${frm.doc.status === "Paid" ? "success" : "warning"}">
                        <div class="stat-value">${frm.doc.amount || 0}</div>
                        <div class="stat-label">${__("Amount")} (${
				frm.doc.currency || "ZMW"
			})</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-value">${frm.doc.visits || 0}</div>
                        <div class="stat-label">${__("Visits")}</div>
                    </div>
                </div>
            `;

			// Add stats section
			if (!$(".usage-stats").length) {
				const $section = $(`
                    <div class="custom-section">
                        <h6 style="margin: 20px 0 15px 0; font-weight: 600; color: #36414c;">
                            ${__("Usage Statistics")}
                        </h6>
                        ${stats_html}
                    </div>
                `);

				// Insert after status indicator
				const $dashboard = $(frm.dashboard.wrapper);
				if ($dashboard.length) {
					$dashboard.append($section);
				}
			}
		},
	});
}

function copy_to_clipboard(text) {
	if (navigator.clipboard && window.isSecureContext) {
		// Use modern clipboard API
		navigator.clipboard.writeText(text);
	} else {
		// Fallback for older browsers
		const temp_input = document.createElement("input");
		temp_input.value = text;
		document.body.appendChild(temp_input);
		temp_input.select();
		document.execCommand("copy");
		document.body.removeChild(temp_input);
	}
}

function send_payment_link_email(frm) {
	frappe.prompt(
		[
			{
				fieldname: "email_address",
				label: __("Email Address"),
				fieldtype: "Data",
				reqd: 1,
				default: frm.doc.customer_email || "",
				description: __("Enter email address to send payment link"),
			},
			{
				fieldname: "subject",
				label: __("Subject"),
				fieldtype: "Data",
				default: __("Payment Request: {0}", [frm.doc.name]),
				reqd: 1,
			},
			{
				fieldname: "message",
				label: __("Message"),
				fieldtype: "Text",
				default: __("Please use the following link to complete your payment of {0} {1}.", [
					frm.doc.amount,
					frm.doc.currency || "ZMW",
				]),
			},
		],
		(values) => {
			if (!isValidEmail(values.email_address)) {
				frappe.msgprint({
					title: __("Invalid Email"),
					indicator: "red",
					message: __("Please enter a valid email address"),
				});
				return;
			}

			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_link.payment_link.send_payment_link_email",
				args: {
					payment_link: frm.doc.name,
					email_address: values.email_address,
					subject: values.subject,
					message: values.message,
				},
				freeze: true,
				freeze_message: __("Sending email..."),
				callback: function (response) {
					if (response.message && response.message.success) {
						frappe.show_alert({
							message: __("Payment link sent via email successfully"),
							indicator: "green",
						});

						// Update customer email if different
						if (values.email_address !== frm.doc.customer_email) {
							frm.set_value("customer_email", values.email_address);
							frm.save();
						}
					} else {
						frappe.msgprint({
							title: __("Email Failed"),
							indicator: "red",
							message: response.message
								? response.message.message || __("Failed to send email")
								: __("Server request failed"),
						});
					}
				},
				error: function () {
					frappe.msgprint({
						title: __("Email Failed"),
						indicator: "red",
						message: __("Failed to connect to email server"),
					});
				},
			});
		},
		__("Send Payment Link via Email"),
		__("Send")
	);
}

function send_payment_link_sms(frm) {
	frappe.prompt(
		[
			{
				fieldname: "phone_number",
				label: __("Phone Number"),
				fieldtype: "Data",
				reqd: 1,
				default: frm.doc.customer_phone || "",
				description: __("Enter phone number with country code (e.g., +260...)"),
			},
			{
				fieldname: "message",
				label: __("Message"),
				fieldtype: "Text",
				default: __("Pay {0} {1} using: {2}", [
					frm.doc.amount,
					frm.doc.currency || "ZMW",
					frm.doc.payment_url,
				]),
			},
		],
		(values) => {
			if (!isValidPhone(values.phone_number)) {
				frappe.msgprint({
					title: __("Invalid Phone Number"),
					indicator: "red",
					message: __("Please enter a valid phone number with country code"),
				});
				return;
			}

			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_link.payment_link.send_payment_link_sms",
				args: {
					payment_link: frm.doc.name,
					phone_number: values.phone_number,
					message: values.message,
				},
				freeze: true,
				freeze_message: __("Sending SMS..."),
				callback: function (response) {
					if (response.message && response.message.success) {
						frappe.show_alert({
							message: __("Payment link sent via SMS successfully"),
							indicator: "green",
						});

						// Update customer phone if different
						if (values.phone_number !== frm.doc.customer_phone) {
							frm.set_value("customer_phone", values.phone_number);
							frm.save();
						}
					} else {
						frappe.msgprint({
							title: __("SMS Failed"),
							indicator: "red",
							message: response.message
								? response.message.message || __("Failed to send SMS")
								: __("Server request failed"),
						});
					}
				},
				error: function () {
					frappe.msgprint({
						title: __("SMS Failed"),
						indicator: "red",
						message: __("Failed to connect to SMS gateway"),
					});
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
				freeze: true,
				freeze_message: __("Cancelling payment link..."),
				callback: function (response) {
					if (response.message && response.message.success) {
						frappe.show_alert({
							message: __("Payment link cancelled successfully"),
							indicator: "green",
						});
						frm.reload_doc();
					} else {
						frappe.msgprint({
							title: __("Cancellation Failed"),
							indicator: "red",
							message: response.message
								? response.message.message || __("Failed to cancel payment link")
								: __("Server request failed"),
						});
					}
				},
			});
		}
	);
}

function create_new_payment_link(frm) {
	frappe.confirm(__("Create a new payment link based on this one?"), function () {
		frappe.new_doc("Payment Link", {
			amount: frm.doc.amount,
			currency: frm.doc.currency,
			customer_name: frm.doc.customer_name,
			customer_email: frm.doc.customer_email,
			customer_phone: frm.doc.customer_phone,
			description: frm.doc.description,
			expiry_date: frappe.datetime.add_days(new Date(), 7), // Default 7 days expiry
		});
	});
}

function duplicate_payment_link(frm) {
	frappe.route_options = {
		amount: frm.doc.amount,
		currency: frm.doc.currency,
		customer_name: frm.doc.customer_name,
		customer_email: frm.doc.customer_email,
		customer_phone: frm.doc.customer_phone,
		description: frm.doc.description,
	};
	frappe.new_doc("Payment Link");
}

function isValidEmail(email) {
	const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	return re.test(email);
}

function isValidPhone(phone) {
	// Basic phone validation - adjust for Zambia phone numbers
	const re = /^\+?[0-9\s\-\(\)]{10,}$/;
	return re.test(phone);
}

// =============================================
// LIST VIEW SCRIPT - Payment Link
// =============================================

frappe.listview_settings["Payment Link"] = {
	add_fields: ["status", "amount", "currency", "payment_url", "expiry_date", "customer_name"],

	// Set default filters to show all records
	filters: [
		// No default filters
	],

	get_indicator: function (doc) {
		const status_colors = {
			Pending: ["orange", "orange"],
			Paid: ["green", "lightgreen"],
			Failed: ["red", "lightcoral"],
			Cancelled: ["grey", "lightgrey"],
			Expired: ["darkgrey", "lightgrey"],
		};

		const color = status_colors[doc.status] || ["grey", "lightgrey"];
		return [__(doc.status), color[0], "status,=," + doc.status];
	},

	onload: function (listview) {
		// Ensure list is properly loaded
		listview.page.add_inner_button(
			__("Refresh"),
			function () {
				listview.refresh();
			},
			__("Tools")
		);

		// Add custom filter buttons for quick filtering
		add_quick_filter_buttons(listview);

		// Add custom buttons to list view menu
		listview.page.add_menu_item(
			__("Create Payment Link"),
			function () {
				frappe.new_doc("Payment Link");
			},
			false,
			__("Create")
		);

		listview.page.add_menu_item(
			__("Bulk Send Email"),
			function () {
				bulk_send_email(listview);
			},
			false,
			__("Tools")
		);

		listview.page.add_menu_item(
			__("Export Links"),
			function () {
				export_payment_links(listview);
			},
			false,
			__("Tools")
		);

		listview.page.add_menu_item(
			__("Show All"),
			function () {
				clear_all_filters(listview);
			},
			false,
			__("View")
		);

		// Add empty state handler
		handle_empty_state(listview);

		// Debug logging
		console.log("Payment Link ListView Loaded");
		console.log("Current filters:", listview.filter_list.get_filters());
	},

	formatters: {
		status: function (value) {
			const status_icons = {
				Pending: '<i class="fa fa-clock-o text-warning"></i>',
				Paid: '<i class="fa fa-check-circle text-success"></i>',
				Failed: '<i class="fa fa-times-circle text-danger"></i>',
				Cancelled: '<i class="fa fa-ban text-muted"></i>',
				Expired: '<i class="fa fa-calendar-times-o text-muted"></i>',
			};
			return (status_icons[value] || "") + " " + __(value);
		},

		amount: function (value, df, doc) {
			if (!value) return "";
			const currency = doc.currency || "ZMW";
			const formatted_amount = parseFloat(value).toLocaleString("en-US", {
				minimumFractionDigits: 2,
				maximumFractionDigits: 2,
			});

			const status_class =
				doc.status === "Paid"
					? "text-success"
					: doc.status === "Pending"
					? "text-warning"
					: "text-muted";

			return `<span class="pull-right ${status_class}" style="font-weight: 600;">
                ${currency} ${formatted_amount}
            </span>`;
		},

		expiry_date: function (value, df, doc) {
			if (!value) return "";

			const expiry_date = new Date(value);
			const now = new Date();
			const days_until_expiry = Math.ceil((expiry_date - now) / (1000 * 60 * 60 * 24));

			let badge_class = "badge-success";
			let badge_text = __("Valid");

			if (days_until_expiry <= 0) {
				badge_class = "badge-danger";
				badge_text = __("Expired");
			} else if (days_until_expiry <= 1) {
				badge_class = "badge-warning";
				badge_text = __("Expires today");
			} else if (days_until_expiry <= 3) {
				badge_class = "badge-warning";
				badge_text = __("Expires soon");
			}

			return `
                <div class="clearfix">
                    <span class="pull-left">${frappe.datetime.str_to_user(value)}</span>
                    <span class="pull-right badge ${badge_class}">${badge_text}</span>
                </div>
            `;
		},

		payment_url: function (value, df, doc) {
			if (!value) return "";

			const is_active =
				doc.status === "Pending" &&
				(!doc.expiry_date || new Date(doc.expiry_date) > new Date());

			return `
                <div class="clearfix">
                    <small style="word-break: break-all; color: ${
						is_active ? "#5e64ff" : "#8d99a6"
					}">
                        ${value.substring(0, 50)}${value.length > 50 ? "..." : ""}
                    </small>
                    ${
						is_active
							? `
                        <button class="btn btn-xs btn-default pull-right btn-copy-list"
                                data-url="${value}"
                                style="margin-top: -3px;">
                            <i class="fa fa-copy"></i>
                        </button>
                    `
							: ""
					}
                </div>
            `;
		},
	},

	initial_sort_by: "creation",
	initial_sort_order: "desc",

	refresh: function (listview) {
		// Update record count
		update_record_count(listview);

		// Bind copy buttons
		bind_copy_buttons(listview);

		// Handle empty state
		handle_empty_state(listview);

		// Auto-refresh for pending links
		const has_pending = listview.data.some((doc) => doc.status === "Pending");
		if (has_pending && !listview.auto_refresh_interval) {
			listview.auto_refresh_interval = setInterval(function () {
				if (listview.$list) {
					console.log("Auto-refreshing payment links list...");
					listview.refresh();
				}
			}, 60000); // 60 seconds
		}
	},

	before_reload: function (listview) {
		if (listview.auto_refresh_interval) {
			clearInterval(listview.auto_refresh_interval);
			listview.auto_refresh_interval = null;
		}
	},
};

function add_quick_filter_buttons(listview) {
	const filters_container = listview.page.$(".list-filters");

	if (!filters_container.length) return;

	const quick_filters = [
		{
			label: __("Active"),
			filter: [
				["status", "=", "Pending"],
				["expiry_date", ">", frappe.datetime.now_datetime()],
			],
			color: "orange",
		},
		{
			label: __("Paid"),
			filter: [["status", "=", "Paid"]],
			color: "green",
		},
		{
			label: __("Expired"),
			filter: [["expiry_date", "<", frappe.datetime.now_datetime()]],
			color: "grey",
		},
		{
			label: __("Today"),
			filter: [
				[
					"creation",
					"Between",
					[frappe.datetime.get_today(), frappe.datetime.get_today()],
				],
			],
			color: "blue",
		},
		{
			label: __("This Week"),
			filter: [["creation", "This Week"]],
			color: "green",
		},
	];

	// Create quick filter buttons container
	const $quick_filters = $(`
        <div class="quick-filter-buttons" style="
            margin: 10px 0;
            padding: 10px;
            background: #f5f7fa;
            border-radius: 4px;
            border: 1px solid #d1d8dd;
        ">
            <strong style="margin-right: 10px;">${__("Quick Filters:")}</strong>
        </div>
    `);

	filters_container.prepend($quick_filters);

	// Add filter buttons
	quick_filters.forEach((filter) => {
		const $button = $(`
            <button class="btn btn-default btn-xs"
                style="margin-right: 5px; margin-bottom: 5px;
                ${filter.color ? `border-left: 3px solid ${filter.color};` : ""}">
                ${filter.label}
            </button>
        `);

		$button.click(function () {
			listview.filter_list.clear_filters();
			filter.filter.forEach((f) => {
				listview.filter_list.add_filter(f[0], f[1], f[2]);
			});
			listview.refresh();
		});

		$quick_filters.append($button);
	});

	// Add clear filter button
	const $clear_button = $(`
        <button class="btn btn-default btn-xs" style="margin-bottom: 5px;">
            <i class="fa fa-times"></i> ${__("Clear Filters")}
        </button>
    `);

	$clear_button.click(function () {
		clear_all_filters(listview);
	});

	$quick_filters.append($clear_button);
}

function clear_all_filters(listview) {
	listview.filter_list.clear_filters();
	listview.refresh();
	frappe.show_alert({
		message: __("All filters cleared"),
		indicator: "blue",
	});
}

function handle_empty_state(listview) {
	// Check if list is empty
	const checkEmptyState = function () {
		const $list_body = listview.$list.find(".list-body");
		const has_rows = $list_body.find(".list-row").length > 0;

		if (!has_rows) {
			// Remove existing empty state message
			$list_body.find(".empty-state-message").remove();

			// Create empty state message
			const empty_state_html = `
                <div class="empty-state-message" style="
                    text-align: center;
                    padding: 60px 20px;
                    color: #8d99a6;
                ">
                    <div style="font-size: 72px; margin-bottom: 20px; color: #d1d8dd;">
                        <i class="fa fa-link"></i>
                    </div>
                    <h4 style="margin-bottom: 15px; color: #6c7680;">
                        ${__("No Payment Links Found")}
                    </h4>
                    <p style="margin-bottom: 25px; max-width: 500px; margin-left: auto; margin-right: auto;">
                        ${__(
							"You haven't created any payment links yet. Create your first payment link to start accepting payments."
						)}
                    </p>
                    <button class="btn btn-primary btn-create-first">
                        <i class="fa fa-plus"></i> ${__("Create Payment Link")}
                    </button>
                </div>
            `;

			$list_body.html(empty_state_html);

			// Bind create button
			$list_body.find(".btn-create-first").click(function () {
				frappe.new_doc("Payment Link");
			});
		}
	};

	// Check on load and after refresh
	setTimeout(checkEmptyState, 500);
	listview.$list.on("list:refresh", checkEmptyState);
}

function update_record_count(listview) {
	setTimeout(function () {
		const count = listview.data ? listview.data.length : 0;
		const $count_element = listview.page.$(".list-count");

		if ($count_element.length) {
			$count_element.text(__("{0} payment links", [count]));
		}

		// Update page title with count
		const $page_title = listview.page.$(".title-text");
		if ($page_title.length && count > 0) {
			$page_title.text(__("Payment Links") + ` (${count})`);
		}

		console.log(`Total payment links: ${count}`);
	}, 500);
}

function bind_copy_buttons(listview) {
	// Remove existing click handlers
	listview.$list.find(".btn-copy-list").off("click");

	// Add new click handlers
	listview.$list.find(".btn-copy-list").click(function () {
		const url = $(this).data("url");
		if (url) {
			copy_to_clipboard(url);
			frappe.show_alert({
				message: __("Payment URL copied to clipboard"),
				indicator: "green",
			});
		}
	});
}

function bulk_send_email(listview) {
	// Get selected rows
	const selected_rows = listview.get_checked_items();

	if (selected_rows.length === 0) {
		frappe.msgprint({
			title: __("No Selection"),
			indicator: "orange",
			message: __("Please select payment links to send emails"),
		});
		return;
	}

	frappe.prompt(
		{
			fieldname: "email_template",
			label: __("Email Template"),
			fieldtype: "Link",
			options: "Email Template",
			reqd: 1,
			get_query: function () {
				return {
					filters: {
						reference_doctype: "Payment Link",
					},
				};
			},
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_link.payment_link.bulk_send_emails",
				args: {
					payment_links: selected_rows.map((row) => row.name),
					email_template: values.email_template,
				},
				freeze: true,
				freeze_message: __("Sending emails..."),
				callback: function (response) {
					if (response.message && response.message.success) {
						frappe.show_alert({
							message: __("Emails sent to {0} recipients", [selected_rows.length]),
							indicator: "green",
						});
						listview.uncheck_all();
					} else {
						frappe.msgprint({
							title: __("Bulk Send Failed"),
							indicator: "red",
							message: response.message
								? response.message.message || __("Failed to send emails")
								: __("Server request failed"),
						});
					}
				},
			});
		},
		__("Bulk Send Email"),
		__("Send")
	);
}

function export_payment_links(listview) {
	frappe.prompt(
		[
			{
				fieldname: "date_range",
				label: __("Date Range"),
				fieldtype: "DateRange",
				reqd: 1,
			},
			{
				fieldname: "status",
				label: __("Status"),
				fieldtype: "MultiSelect",
				options: "\nPending\nPaid\nFailed\nCancelled\nExpired",
			},
			{
				fieldname: "format",
				label: __("Format"),
				fieldtype: "Select",
				options: "CSV\nExcel",
				default: "CSV",
			},
		],
		(values) => {
			const filters = [];

			if (values.date_range && values.date_range.length === 2) {
				filters.push([
					"creation",
					"between",
					[values.date_range[0], values.date_range[1]],
				]);
			}

			if (values.status) {
				const statuses = values.status.split("\n").filter((s) => s);
				if (statuses.length > 0) {
					filters.push(["status", "in", statuses]);
				}
			}

			frappe.call({
				method: "frappe.desk.query_report.get_script_report",
				args: {
					report_name: "Payment Link Summary",
					filters: filters,
					format: values.format.toLowerCase(),
				},
				freeze: true,
				freeze_message: __("Exporting payment links..."),
				callback: function (response) {
					if (response.message) {
						// Create download link
						const data = response.message;
						const filename = `payment_links_${frappe.datetime.get_today()}.${values.format.toLowerCase()}`;

						if (typeof data === "string") {
							const blob = new Blob([data], {
								type:
									values.format === "Excel"
										? "application/vnd.ms-excel"
										: "text/csv;charset=utf-8;",
							});
							const link = document.createElement("a");

							if (link.download !== undefined) {
								const url = URL.createObjectURL(blob);
								link.setAttribute("href", url);
								link.setAttribute("download", filename);
								link.style.visibility = "hidden";
								document.body.appendChild(link);
								link.click();
								document.body.removeChild(link);
							}

							frappe.show_alert({
								message: __("Payment links exported successfully"),
								indicator: "green",
							});
						}
					}
				},
			});
		},
		__("Export Payment Links"),
		__("Export")
	);
}

// Add list view CSS
function add_listview_css() {
	const css = `
        .payment-link-list .list-row {
            border-left: 4px solid #d1d8dd;
            transition: all 0.2s ease;
        }

        .payment-link-list .list-row:hover {
            background-color: #f5f7fa;
            transform: translateX(2px);
        }

        .payment-link-list .list-row[data-status="Pending"] {
            border-left-color: #f0ad4e;
        }

        .payment-link-list .list-row[data-status="Paid"] {
            border-left-color: #5cb85c;
        }

        .payment-link-list .list-row[data-status="Failed"] {
            border-left-color: #d9534f;
        }

        .payment-link-list .list-row[data-status="Cancelled"],
        .payment-link-list .list-row[data-status="Expired"] {
            border-left-color: #777;
        }

        .list-row-col .btn-copy-list {
            opacity: 0;
            transition: opacity 0.2s ease;
        }

        .list-row:hover .btn-copy-list {
            opacity: 1;
        }

        .empty-state-message .btn-create-first {
            padding: 10px 30px;
            font-size: 16px;
        }

        .badge {
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 10px;
        }

        .badge-success {
            background-color: #d4edda;
            color: #155724;
        }

        .badge-warning {
            background-color: #fff3cd;
            color: #856404;
        }

        .badge-danger {
            background-color: #f8d7da;
            color: #721c24;
        }
    `;

	if (!document.getElementById("payment-link-list-css")) {
		const style = document.createElement("style");
		style.id = "payment-link-list-css";
		style.textContent = css;
		document.head.appendChild(style);
	}
}

// Initialize CSS when page loads
$(document).on("list-load", function (e, listview) {
	if (listview && listview.doctype === "Payment Link") {
		add_listview_css();

		// Add status data attribute to rows
		listview.$list.on("list:row_render", function (e, $row, data) {
			if (data.status) {
				$row.attr("data-status", data.status);
			}
		});
	}
});
