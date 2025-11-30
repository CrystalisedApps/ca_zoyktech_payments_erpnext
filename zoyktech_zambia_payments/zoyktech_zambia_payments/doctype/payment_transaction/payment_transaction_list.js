frappe.listview_settings["Payment Transaction"] = {
	add_fields: ["status", "amount", "currency", "payment_method"],
	get_indicator: function (doc) {
		const status_colors = {
			Completed: "green",
			Pending: "orange",
			Failed: "red",
			Refunded: "blue",
			Cancelled: "grey",
		};

		return [__(doc.status), status_colors[doc.status] || "grey", "status,=," + doc.status];
	},

	onload: function (listview) {
		// Add custom buttons to list view
		listview.page.add_menu_item(__("Export Payment Report"), function () {
			export_payment_report(listview);
		});

		listview.page.add_menu_item(__("Reconcile Payments"), function () {
			reconcile_payments(listview);
		});
	},

	button: {
		show: function (doc) {
			return doc.status === "Pending";
		},
		get_label: function () {
			return __("Check Status");
		},
		get_description: function (doc) {
			return __("Check current payment status with gateway");
		},
		action: function (doc) {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.api.routes.get_payment_status",
				args: {
					reference_id: doc.reference_id,
				},
				callback: function (response) {
					if (response.message.success) {
						frappe.show_alert({
							message: __("Status checked: {0}", [response.message.status]),
							indicator: "green",
						});
						frappe.route_options = { status: doc.status };
						frappe.set_route("List", "Payment Transaction");
					}
				},
			});
		},
	},
};

function export_payment_report(listview) {
	frappe.prompt(
		{
			fieldname: "days",
			label: __("Last N Days"),
			fieldtype: "Int",
			default: 30,
			reqd: 1,
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.export_payment_report",
				args: {
					days: values.days,
					format_type: "csv",
				},
				callback: function (response) {
					if (response.message.success) {
						// Create and download CSV file
						const blob = new Blob([response.message.data], { type: "text/csv" });
						const url = window.URL.createObjectURL(blob);
						const a = document.createElement("a");
						a.href = url;
						a.download = response.message.filename;
						a.click();
						window.URL.revokeObjectURL(url);

						frappe.show_alert({
							message: __("Report exported successfully"),
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: __("Export Failed"),
							indicator: "red",
							message: response.message.error || __("Failed to export report"),
						});
					}
				},
			});
		},
		__("Export Payment Report"),
		__("Export")
	);
}

function reconcile_payments(listview) {
	frappe.confirm(
		__(
			"This will check the status of all pending payments with the payment gateway. Continue?"
		),
		function () {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.scheduled_tasks.check_pending_payments",
				callback: function (response) {
					frappe.show_alert({
						message: __("Payment reconciliation completed"),
						indicator: "green",
					});
					listview.refresh();
				},
			});
		}
	);
}

// Custom filter for payment transactions
frappe.listview_settings["Payment Transaction"].filters = [
	{
		fieldname: "status",
		label: __("Status"),
		fieldtype: "Select",
		options: "\nPending\nCompleted\nFailed\nRefunded\nCancelled",
	},
	{
		fieldname: "payment_method",
		label: __("Payment Method"),
		fieldtype: "Select",
		options: "\nMTN Mobile Money\nAirtel Money\nCard Payment\nBank Transfer",
	},
	{
		fieldname: "payment_completed",
		label: __("Payment Date"),
		fieldtype: "Date",
		options: "payment_completed",
	},
];
