// payment_gateway_settings.js - Bulletproof Version
// This should work on all Frappe versions

frappe.ui.form.on("Payment Gateway Settings", {
	refresh: function (frm) {
		// Method 1: Standard custom buttons
		setTimeout(function () {
			add_action_buttons(frm);
		}, 100);

		// Update default payment method dropdown
		update_payment_method_options(frm);
	},

	gateway_name: function (frm) {
		toggle_gateway_fields(frm);
	},

	is_test_mode: function (frm) {
		toggle_test_mode_fields(frm);
	},

	enabled_payment_methods_add: function (frm, cdt, cdn) {
		setTimeout(function () {
			update_payment_method_options(frm);
		}, 300);
	},

	enabled_payment_methods_remove: function (frm, cdt, cdn) {
		setTimeout(function () {
			update_payment_method_options(frm);
		}, 300);
	},
});

// Listen to child table changes
frappe.ui.form.on("Payment Method", {
	payment_method: function (frm, cdt, cdn) {
		setTimeout(function () {
			update_payment_method_options(frm);
		}, 300);
	},

	enabled: function (frm, cdt, cdn) {
		setTimeout(function () {
			update_payment_method_options(frm);
		}, 300);
	},
});

function add_action_buttons(frm) {
	if (frm.is_new()) return;

	// Clear existing custom buttons
	frm.clear_custom_buttons();

	// Add buttons - try multiple methods for compatibility

	// Test Connection
	frm.add_custom_button(
		__("Test Connection"),
		function () {
			test_connection(frm);
		},
		__("Actions")
	);

	// Sync Methods
	frm.add_custom_button(
		__("Sync Methods"),
		function () {
			sync_payment_methods(frm);
		},
		__("Actions")
	);

	// Clear Cache
	frm.add_custom_button(
		__("Clear Cache"),
		function () {
			clear_cache(frm);
		},
		__("Actions")
	);

	// View Methods
	frm.add_custom_button(
		__("View Methods"),
		function () {
			view_configured_methods(frm);
		},
		__("Actions")
	);

	// Summary
	frm.add_custom_button(
		__("Summary"),
		function () {
			view_settings_summary(frm);
		},
		__("Actions")
	);
}

function test_connection(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_gateway_settings.payment_gateway_settings.test_gateway_connection",
		freeze: true,
		freeze_message: __("Testing connection..."),
		callback: function (r) {
			if (r.message && r.message.success) {
				var details = r.message.details || {};
				frappe.msgprint({
					title: __("Connection Test"),
					indicator: "green",
					message: `
                        <div class="alert alert-success">
                            <h5>✅ ${__("Connection Successful")}</h5>
                            <p><strong>${__("URL")}:</strong> ${details.base_url || "N/A"}</p>
                            <p><strong>${__("Test Mode")}:</strong> ${
						details.test_mode ? __("Yes") : __("No")
					}</p>
                        </div>
                    `,
				});
			} else {
				frappe.msgprint({
					title: __("Connection Failed"),
					indicator: "red",
					message: r.message ? r.message.message : __("Connection failed"),
				});
			}
		},
	});
}

function sync_payment_methods(frm) {
	frappe.confirm(__("This will sync all payment methods. Continue?"), function () {
		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_gateway_settings.payment_gateway_settings.sync_payment_methods",
			freeze: true,
			freeze_message: __("Syncing payment methods..."),
			callback: function (r) {
				if (r.message && r.message.success) {
					frappe.show_alert(
						{
							message: __("✅ Synced successfully"),
							indicator: "green",
						},
						5
					);
					frm.reload_doc();
				} else {
					frappe.msgprint({
						title: __("Sync Failed"),
						indicator: "red",
						message: r.message ? r.message.message : __("Sync failed"),
					});
				}
			},
		});
	});
}

function clear_cache(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_gateway_settings.payment_gateway_settings.clear_cache",
		callback: function (r) {
			if (r.message && r.message.success) {
				frappe.show_alert(
					{
						message: __("✅ Cache cleared"),
						indicator: "green",
					},
					3
				);
			}
		},
	});
}

function view_configured_methods(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_gateway_settings.payment_gateway_settings.get_configured_methods",
		callback: function (r) {
			if (r.message && r.message.success) {
				var methods = r.message.methods;

				if (methods.length === 0) {
					frappe.msgprint(__("No payment methods configured"));
					return;
				}

				var html =
					'<table class="table table-bordered"><thead><tr>' +
					"<th>" +
					__("Method") +
					"</th>" +
					"<th>" +
					__("Gateway") +
					"</th>" +
					"<th>" +
					__("Min") +
					"</th>" +
					"<th>" +
					__("Max") +
					"</th>" +
					"<th>" +
					__("Fees") +
					"</th>" +
					"</tr></thead><tbody>";

				methods.forEach(function (m) {
					html +=
						"<tr>" +
						"<td><strong>" +
						(m.payment_method || "") +
						"</strong></td>" +
						"<td>" +
						(m.payment_gateway || "") +
						"</td>" +
						"<td>ZMW " +
						(m.minimum_amount || 0).toFixed(2) +
						"</td>" +
						"<td>ZMW " +
						(m.maximum_amount || 0).toFixed(2) +
						"</td>" +
						"<td>" +
						(m.processing_fee_percentage || 0) +
						"% + ZMW " +
						(m.fixed_fee || 0).toFixed(2) +
						"</td>" +
						"</tr>";
				});

				html += "</tbody></table>";
				html +=
					'<p class="text-muted"><small>Total: ' +
					methods.length +
					" methods</small></p>";

				frappe.msgprint({
					title: __("Configured Payment Methods"),
					message: html,
					wide: true,
				});
			}
		},
	});
}

function view_settings_summary(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_gateway_settings.payment_gateway_settings.get_settings_summary",
		callback: function (r) {
			if (r.message && r.message.success) {
				var d = r.message;
				var html =
					'<table class="table table-bordered">' +
					'<tr><td width="200"><strong>' +
					__("Gateway") +
					"</strong></td><td>" +
					(d.gateway_name || "-") +
					"</td></tr>" +
					"<tr><td><strong>" +
					__("Test Mode") +
					"</strong></td><td>" +
					(d.is_test_mode ? "✅ Yes" : "❌ No") +
					"</td></tr>" +
					"<tr><td><strong>" +
					__("Configured Methods") +
					"</strong></td><td>" +
					(d.configured_methods || 0) +
					"</td></tr>" +
					"<tr><td><strong>" +
					__("Default Method") +
					"</strong></td><td>" +
					(d.default_method || "-") +
					"</td></tr>" +
					"<tr><td><strong>" +
					__("Link Expiry") +
					"</strong></td><td>" +
					(d.payment_link_expiry_days || 0) +
					" days</td></tr>" +
					"<tr><td><strong>" +
					__("Auto-create Links") +
					"</strong></td><td>" +
					(d.auto_create_links ? "✅ Yes" : "❌ No") +
					"</td></tr>" +
					"<tr><td><strong>" +
					__("Email Notifications") +
					"</strong></td><td>" +
					(d.email_notifications ? "✅ Yes" : "❌ No") +
					"</td></tr>" +
					"<tr><td><strong>" +
					__("SMS Notifications") +
					"</strong></td><td>" +
					(d.sms_notifications ? "✅ Yes" : "❌ No") +
					"</td></tr>" +
					"</table>";

				frappe.msgprint({
					title: __("Settings Summary"),
					message: html,
					wide: true,
				});
			}
		},
	});
}

function update_payment_method_options(frm) {
	// Build options directly from child table
	var options = [""];
	var seen = {};

	if (frm.doc.enabled_payment_methods && frm.doc.enabled_payment_methods.length > 0) {
		frm.doc.enabled_payment_methods.forEach(function (row) {
			// Only add if enabled and not already added
			if (row.payment_method && row.enabled !== 0 && !seen[row.payment_method]) {
				options.push(row.payment_method);
				seen[row.payment_method] = true;
			}
		});
	}

	// Sort alphabetically (keep empty option first)
	var sorted_options = options.slice(1).sort();
	options = [""].concat(sorted_options);

	// Update field
	var options_str = options.join("\n");
	frm.set_df_property("default_payment_method", "options", options_str);
	frm.refresh_field("default_payment_method");

	// Clear if current value not in options
	if (frm.doc.default_payment_method && options.indexOf(frm.doc.default_payment_method) === -1) {
		frm.set_value("default_payment_method", "");
	}
}

function toggle_gateway_fields(frm) {
	var is_zoyktech = frm.doc.gateway_name === "ZoykTech";
	frm.toggle_display("section_break_1", is_zoyktech);
	frm.toggle_reqd("api_key", is_zoyktech);
	frm.toggle_reqd("secret_key", is_zoyktech);
	frm.toggle_reqd("base_url", is_zoyktech);
}

function toggle_test_mode_fields(frm) {
	frm.toggle_display("test_base_url", frm.doc.is_test_mode);
	frm.toggle_reqd("test_base_url", frm.doc.is_test_mode);
}
