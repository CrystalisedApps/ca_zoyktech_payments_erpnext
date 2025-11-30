frappe.provide("zoyktech_zambia_payments.dashboard");

zoyktech_zambia_payments.dashboard.PaymentDashboard = class {
	constructor() {
		this.init();
	}

	init() {
		this.load_dashboard_data();
		this.setup_real_time_updates();
	}

	load_dashboard_data() {
		frappe.call({
			method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.dashboard.get_dashboard_data",
			callback: (response) => {
				if (response.message) {
					this.render_dashboard(response.message);
				}
			},
		});
	}

	render_dashboard(data) {
		this.render_summary_cards(data);
		this.render_recent_transactions(data.recent_transactions);
		this.render_payment_methods_chart(data.payment_methods_breakdown);
		this.render_daily_collections_chart(data.daily_collections);
	}

	render_summary_cards(data) {
		// Update summary cards
		this.update_card_value("#total-collections", data.total_collections, true);
		this.update_card_value("#successful-payments", data.successful_payments, false);
		this.update_card_value("#failed-payments", data.failed_payments, false);
		this.update_card_value("#pending-payments", data.pending_payments, false);
	}

	update_card_value(selector, value, is_currency) {
		const element = document.querySelector(selector);
		if (element) {
			if (is_currency) {
				element.textContent = this.format_currency(value);
			} else {
				element.textContent = value.toLocaleString();
			}
		}
	}

	render_recent_transactions(transactions) {
		const container = document.getElementById("recent-transactions-list");
		if (!container) return;

		let html = "";

		transactions.forEach((transaction) => {
			const status_badge = this.get_status_badge(transaction.status);
			const amount = this.format_currency(transaction.amount);
			const date = this.format_date(transaction.payment_completed);

			html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${transaction.reference_id}</h6>
                            <small class="text-muted">${
								transaction.customer_email || "N/A"
							}</small>
                        </div>
                        <div class="text-right">
                            <div class="fw-bold">${amount}</div>
                            <div>${status_badge}</div>
                            <small class="text-muted">${date}</small>
                        </div>
                    </div>
                </div>
            `;
		});

		container.innerHTML = html;
	}

	render_payment_methods_chart(breakdown) {
		// This would render a chart using Chart.js or similar
		// For now, just log the data
		console.log("Payment methods breakdown:", breakdown);
	}

	render_daily_collections_chart(daily_data) {
		// This would render a line chart for daily collections
		console.log("Daily collections:", daily_data);
	}

	format_currency(amount) {
		return new Intl.NumberFormat("en-ZM", {
			style: "currency",
			currency: "ZMW",
		}).format(amount);
	}

	format_date(date_string) {
		if (!date_string) return "N/A";
		return new Date(date_string).toLocaleDateString("en-ZM");
	}

	get_status_badge(status) {
		const status_classes = {
			Completed: "badge-success",
			Pending: "badge-warning",
			Failed: "badge-danger",
			Cancelled: "badge-secondary",
		};

		const cls = status_classes[status] || "badge-secondary";
		return `<span class="badge ${cls}">${status}</span>`;
	}

	setup_real_time_updates() {
		// Listen for real-time payment updates
		frappe.realtime.on("payment_completed", (data) => {
			this.refresh_dashboard();
		});

		frappe.realtime.on("payment_failed", (data) => {
			this.refresh_dashboard();
		});
	}

	refresh_dashboard() {
		this.load_dashboard_data();
	}
};

// Initialize dashboard when page loads
frappe.ready(function () {
	if (document.getElementById("payment-dashboard")) {
		window.paymentDashboard = new zoyktech_zambia_payments.dashboard.PaymentDashboard();
	}
});
