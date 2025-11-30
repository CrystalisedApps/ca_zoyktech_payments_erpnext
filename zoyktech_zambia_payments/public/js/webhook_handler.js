frappe.provide("zoyktech_zambia_payments.webhook");

zoyktech_zambia_payments.webhook.WebhookHandler = class {
	constructor() {
		this.init();
	}

	init() {
		this.setup_webhook_testing();
		this.setup_webhook_logs();
	}

	setup_webhook_testing() {
		// Test webhook functionality
		$(document).on("click", ".btn-test-webhook", () => {
			this.test_webhook();
		});
	}

	setup_webhook_logs() {
		// Load webhook logs
		this.load_webhook_logs();
	}

	test_webhook() {
		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks.test_webhook",
			args: {
				test_type: "success",
			},
			callback: (response) => {
				if (response.message.success) {
					frappe.show_alert({
						message: __("Webhook test completed successfully"),
						indicator: "green",
					});
				} else {
					frappe.show_alert({
						message: __("Webhook test failed: " + response.message.message),
						indicator: "red",
					});
				}
			},
		});
	}

	load_webhook_logs() {
		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks.get_webhook_logs",
			args: {
				days: 7,
			},
			callback: (response) => {
				this.render_webhook_logs(response.message);
			},
		});
	}

	render_webhook_logs(logs) {
		const container = document.getElementById("webhook-logs-container");
		if (!container) return;

		let html = "";

		logs.forEach((log) => {
			const timestamp = this.format_datetime(log.creation);
			const is_error = log.error && log.error.length > 0;

			html += `
                <div class="list-group-item ${is_error ? "list-group-item-danger" : ""}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${log.method || "Unknown"}</h6>
                            <p class="mb-1">${log.error || "No errors"}</p>
                            <small class="text-muted">${timestamp}</small>
                        </div>
                        <span class="badge ${is_error ? "badge-danger" : "badge-success"}">
                            ${is_error ? "Error" : "Success"}
                        </span>
                    </div>
                </div>
            `;
		});

		container.innerHTML = html;
	}

	format_datetime(datetime_string) {
		return new Date(datetime_string).toLocaleString("en-ZM");
	}

	simulate_webhook_event(event_type, data) {
		// Simulate webhook events for testing
		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.webhooks.simulate_webhook",
			args: {
				event_type: event_type,
				data: data,
			},
			callback: (response) => {
				if (response.message.success) {
					frappe.show_alert({
						message: __("Webhook simulation completed"),
						indicator: "green",
					});
				}
			},
		});
	}
};

// Initialize webhook handler
frappe.ready(function () {
	if (document.querySelector("[data-webhook-section]")) {
		window.webhookHandler = new zoyktech_zambia_payments.webhook.WebhookHandler();
	}
});
