// =============================================
// PRE-EMPTIVE LIST VIEW OVERRIDE
// =============================================

// Store the original frappe.views.ListView class
const OriginalListView = frappe.views.ListView;

// Override the ListView class to intercept Payment Transaction
frappe.views.ListView = class CustomListView extends OriginalListView {
	constructor(opts) {
		super(opts);

		// Check if this is Payment Transaction list
		if (this.doctype === "Payment Transaction") {
			console.log("Intercepted Payment Transaction list view creation");

			// Store reference globally
			window.payment_transaction_listview = this;

			// Override the make method to inject our empty state early
			this.original_make = this.make;
			this.make = this.custom_make;
		}
	}

	custom_make() {
		// Call original make first
		this.original_make();

		// Then inject our customizations IMMEDIATELY
		setTimeout(() => {
			this.inject_customizations();
		}, 100);
	}

	inject_customizations() {
		console.log("Injecting customizations for Payment Transaction list");

		// 1. Add CSS immediately
		this.add_custom_css();

		// 2. Hide Frappe's default elements
		this.hide_default_elements();

		// 3. Check for empty state and show ours
		this.check_and_show_empty_state();

		// 4. Add custom buttons to page
		this.add_custom_buttons();

		// 5. Setup refresh monitoring
		this.setup_refresh_monitoring();
	}

	add_custom_css() {
		const css = `
            /* Hide Frappe's default empty state and add button */
            .list-view-container[data-doctype="Payment Transaction"] .msg-box.no-result,
            .list-view-container[data-doctype="Payment Transaction"] .list-header .btn-primary {
                display: none !important;
            }
            
            /* Custom empty state styling */
            .custom-payment-transaction-empty-state {
                text-align: center;
                padding: 80px 20px;
                color: #8d99a6;
                min-height: 400px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background: #fff;
                border-radius: 8px;
                margin: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                animation: fadeIn 0.5s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .custom-payment-transaction-empty-state .empty-state-icon {
                font-size: 80px;
                margin-bottom: 20px;
                color: #d1d8dd;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); opacity: 0.8; }
                50% { transform: scale(1.05); opacity: 1; }
                100% { transform: scale(1); opacity: 0.8; }
            }
            
            .custom-payment-transaction-empty-state h3 {
                margin-bottom: 15px;
                color: #36414c;
                font-weight: 400;
                font-size: 24px;
            }
            
            .custom-payment-transaction-empty-state .empty-state-buttons {
                margin-top: 20px;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                justify-content: center;
            }
            
            .custom-payment-transaction-empty-state .btn-empty-state {
                padding: 12px 30px;
                font-size: 16px;
                border-radius: 6px;
                transition: all 0.2s ease;
            }
            
            .custom-payment-transaction-empty-state .btn-empty-state:hover {
                transform: translateY(-2px);
            }
            
            .btn-empty-state-primary {
                background: #5e64ff;
                border-color: #5e64ff;
            }
            
            .btn-empty-state-primary:hover {
                background: #4a50e0;
                border-color: #4a50e0;
                box-shadow: 0 4px 12px rgba(94, 100, 255, 0.3);
            }
            
            /* Quick filter buttons styling */
            .payment-transaction-quick-filters {
                margin: 10px 0;
                padding: 10px;
                background: #f5f7fa;
                border-radius: 4px;
                border: 1px solid #d1d8dd;
            }
            
            /* List row styling */
            .list-view-container[data-doctype="Payment Transaction"] .list-row {
                border-left: 4px solid #d1d8dd;
                transition: all 0.2s ease;
            }
            
            .list-view-container[data-doctype="Payment Transaction"] .list-row[data-status="Completed"] {
                border-left-color: #28a745;
            }
            
            .list-view-container[data-doctype="Payment Transaction"] .list-row[data-status="Pending"] {
                border-left-color: #ffc107;
            }
            
            .list-view-container[data-doctype="Payment Transaction"] .list-row[data-status="Failed"] {
                border-left-color: #dc3545;
            }
            
            /* Status indicators in list */
            .list-view-container[data-doctype="Payment Transaction"] .list-row-col .indicator-pill {
                font-size: 11px;
                padding: 2px 8px;
                border-radius: 10px;
                font-weight: 600;
            }
            
            .indicator-pill.green { background: #d4edda; color: #155724; }
            .indicator-pill.orange { background: #fff3cd; color: #856404; }
            .indicator-pill.red { background: #f8d7da; color: #721c24; }
            .indicator-pill.blue { background: #d1ecf1; color: #0c5460; }
            .indicator-pill.grey { background: #e2e3e5; color: #383d41; }
        `;

		// Remove existing if any
		$("#payment-transaction-custom-css").remove();

		const style = document.createElement("style");
		style.id = "payment-transaction-custom-css";
		style.textContent = css;
		document.head.appendChild(style);
	}

	hide_default_elements() {
		// Hide Frappe's "Add Payment Transaction" button
		$(
			'.list-view-container[data-doctype="Payment Transaction"] .list-header .btn-primary'
		).hide();

		// Hide Frappe's default empty state if it exists
		$('.list-view-container[data-doctype="Payment Transaction"] .msg-box.no-result').hide();
	}

	check_and_show_empty_state() {
		const $list_container = $('.list-view-container[data-doctype="Payment Transaction"]');
		if (!$list_container.length) return;

		// Check if list has data
		const has_data = this.data && this.data.length > 0;
		const $list_body = $list_container.find(".list-body");
		const has_rows = $list_body.find(".list-row").length > 0;

		console.log("Empty state check - Has data:", has_data, "Has rows:", has_rows);

		if (!has_data && !has_rows) {
			this.show_empty_state();
		} else {
			this.hide_empty_state();
		}
	}

	show_empty_state() {
		const $list_body = $(
			'.list-view-container[data-doctype="Payment Transaction"] .list-body'
		);
		if (!$list_body.length) return;

		// Remove existing empty state
		$list_body.find(".custom-payment-transaction-empty-state").remove();

		// Create and insert empty state
		const empty_state_html = this.create_empty_state_html();
		$list_body.html(empty_state_html);

		// Bind buttons
		this.bind_empty_state_buttons();
	}

	create_empty_state_html() {
		return `
            <div class="custom-payment-transaction-empty-state">
                <div class="empty-state-icon">
                    <i class="fa fa-exchange"></i>
                </div>
                
                <h3>${__("No Payment Transactions Yet")}</h3>
                
                <p style="
                    margin-bottom: 30px;
                    max-width: 500px;
                    margin-left: auto;
                    margin-right: auto;
                    line-height: 1.6;
                    color: #6c7680;
                    font-size: 15px;
                ">
                    ${__(
						"You haven't processed any payment transactions yet. Transactions will appear here when payments are made through your payment links."
					)}
                </p>
                
                <div class="empty-state-buttons">
                    <button class="btn btn-empty-state btn-empty-state-primary btn-create-transaction">
                        <i class="fa fa-plus"></i> ${__("Create Transaction")}
                    </button>
                    
                    <button class="btn btn-default btn-empty-state btn-create-payment-link">
                        <i class="fa fa-link"></i> ${__("Create Payment Link")}
                    </button>
                </div>
                
                <div style="
                    margin-top: 40px;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 6px;
                    max-width: 600px;
                    text-align: left;
                ">
                    <h5 style="margin-top: 0; margin-bottom: 15px; color: #36414c;">
                        <i class="fa fa-lightbulb-o"></i> ${__("Getting Started")}
                    </h5>
                    <ul style="margin: 0; padding-left: 20px; color: #6c7680;">
                        <li>${__("Create a payment link to share with customers")}</li>
                        <li>${__("Transactions appear automatically when payments are made")}</li>
                        <li>${__("Or create manual transactions for cash/cheque payments")}</li>
                        <li>${__("Use the reconcile feature to update pending transactions")}</li>
                    </ul>
                </div>
            </div>
        `;
	}

	bind_empty_state_buttons() {
		$(".btn-create-transaction")
			.off("click")
			.click(() => {
				frappe.new_doc("Payment Transaction");
			});

		$(".btn-create-payment-link")
			.off("click")
			.click(() => {
				frappe.new_doc("Payment Link");
			});
	}

	hide_empty_state() {
		$(".custom-payment-transaction-empty-state").remove();
	}

	add_custom_buttons() {
		// Add custom buttons to the page
		if (this.page && !this.page.custom_buttons_added) {
			// Add refresh button
			this.page.add_inner_button(__("Refresh"), () => this.refresh(), __("Tools"));

			// Add create button in header (replacing the hidden one)
			this.page.add_inner_button(
				__("Create Transaction"),
				() => frappe.new_doc("Payment Transaction"),
				__("Create")
			);

			this.page.custom_buttons_added = true;
		}
	}

	setup_refresh_monitoring() {
		// Override refresh to check empty state after
		this.original_refresh = this.refresh;
		this.refresh = (...args) => {
			const result = this.original_refresh(...args);

			// Check empty state after refresh
			setTimeout(() => {
				this.check_and_show_empty_state();
			}, 500);

			return result;
		};

		// Monitor data changes
		this.monitor_data_changes();
	}

	monitor_data_changes() {
		// Use MutationObserver to watch for data changes
		const observer = new MutationObserver(() => {
			this.check_and_show_empty_state();
		});

		const list_container = document.querySelector(
			'.list-view-container[data-doctype="Payment Transaction"] .list-body'
		);
		if (list_container) {
			observer.observe(list_container, {
				childList: true,
				subtree: true,
			});
		}
	}
};

// =============================================
// TRADITIONAL LIST VIEW SETTINGS (as fallback)
// =============================================

frappe.listview_settings["Payment Transaction"] = {
	add_fields: ["status", "amount", "currency", "payment_method", "reference_id", "creation"],

	filters: [],

	get_indicator: function (doc) {
		const status_colors = {
			Completed: "green",
			Pending: "orange",
			Failed: "red",
			Refunded: "blue",
			Cancelled: "grey",
			Initiated: "yellow",
			Processing: "blue",
		};
		return [__(doc.status), status_colors[doc.status] || "grey", "status,=," + doc.status];
	},

	onload: function (listview) {
		console.log("Traditional listview_settings onload called");

		// This will work with our overridden ListView class
		// Add any additional traditional settings here

		// Add quick filters
		add_quick_filters(listview);

		// Add export menu item
		listview.page.add_menu_item(
			__("Export Report"),
			() => export_payment_report(listview),
			false,
			__("Tools")
		);
	},

	formatters: {
		status: function (value) {
			const status_icons = {
				Completed: '<i class="fa fa-check-circle text-success"></i>',
				Pending: '<i class="fa fa-clock-o text-warning"></i>',
				Failed: '<i class="fa fa-times-circle text-danger"></i>',
				Refunded: '<i class="fa fa-refresh text-info"></i>',
				Cancelled: '<i class="fa fa-ban text-muted"></i>',
			};
			return (status_icons[value] || "") + " " + __(value);
		},

		amount: function (value, df, doc) {
			if (!value) return "";
			const currency = doc.currency || "ZMW";
			const formatted = parseFloat(value).toLocaleString("en-US", {
				minimumFractionDigits: 2,
				maximumFractionDigits: 2,
			});
			return `<span class="pull-right" style="font-weight: 600;">${currency} ${formatted}</span>`;
		},
	},

	initial_sort_by: "creation",
	initial_sort_order: "desc",

	refresh: function (listview) {
		console.log("Traditional refresh called");
		// This will be called by our overridden refresh method
	},
};

// =============================================
// HELPER FUNCTIONS
// =============================================

function add_quick_filters(listview) {
	// Wait for DOM to be ready
	setTimeout(() => {
		const $filters_container = $(
			'.list-view-container[data-doctype="Payment Transaction"] .list-filters'
		);
		if (!$filters_container.length) return;

		// Remove existing quick filters
		$(".payment-transaction-quick-filters").remove();

		const $quick_filters = $(`
            <div class="payment-transaction-quick-filters">
                <strong style="margin-right: 10px;">${__("Quick Filters:")}</strong>
            </div>
        `);

		$filters_container.prepend($quick_filters);

		const filters = [
			{ label: __("Pending"), status: "Pending", icon: "fa-clock-o", color: "orange" },
			{
				label: __("Completed"),
				status: "Completed",
				icon: "fa-check-circle",
				color: "green",
			},
			{ label: __("Failed"), status: "Failed", icon: "fa-times-circle", color: "red" },
			{ label: __("Today"), type: "today", icon: "fa-calendar", color: "blue" },
		];

		filters.forEach((filter) => {
			const $button = $(`
                <button class="btn btn-default btn-xs" style="margin-right: 5px; margin-bottom: 5px;">
                    <i class="fa ${filter.icon}" style="margin-right: 3px;"></i>
                    ${filter.label}
                </button>
            `);

			$button.click(() => {
				listview.filter_list.clear_filters();
				if (filter.type === "today") {
					listview.filter_list.add_filter("creation", "Between", [
						frappe.datetime.get_today(),
						frappe.datetime.get_today(),
					]);
				} else {
					listview.filter_list.add_filter("status", "=", filter.status);
				}
				listview.refresh();
			});

			$quick_filters.append($button);
		});

		// Add clear button
		const $clear_button = $(`
            <button class="btn btn-default btn-xs" style="margin-bottom: 5px;">
                <i class="fa fa-times"></i> ${__("Clear")}
            </button>
        `);

		$clear_button.click(() => {
			listview.filter_list.clear_filters();
			listview.refresh();
			frappe.show_alert({ message: __("Filters cleared"), indicator: "blue" });
		});

		$quick_filters.append($clear_button);
	}, 1000);
}

function export_payment_report(listview) {
	frappe.prompt(
		{
			fieldname: "date_range",
			label: __("Date Range"),
			fieldtype: "DateRange",
			reqd: 1,
		},
		(values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.export_payment_report",
				args: {
					from_date: values.date_range[0],
					to_date: values.date_range[1],
					format_type: "csv",
				},
				freeze: true,
				freeze_message: __("Generating report..."),
				callback: function (response) {
					if (response.message && response.message.success) {
						const data = response.message.data;
						const filename =
							response.message.filename ||
							`transactions_${frappe.datetime.get_today()}.csv`;

						if (typeof data === "string") {
							const blob = new Blob([data], { type: "text/csv;charset=utf-8;" });
							const url = URL.createObjectURL(blob);
							const a = document.createElement("a");
							a.href = url;
							a.download = filename;
							document.body.appendChild(a);
							a.click();
							document.body.removeChild(a);
							URL.revokeObjectURL(url);

							frappe.show_alert({
								message: __("Report exported"),
								indicator: "green",
							});
						}
					}
				},
			});
		},
		__("Export Report"),
		__("Export")
	);
}

// =============================================
// PAGE LOAD INITIALIZATION
// =============================================

// Run immediately on page load to catch early initialization
$(document).ready(function () {
	console.log("Payment Transaction script loaded");

	// Check if we're already on Payment Transaction list
	if (window.location.pathname.includes("/payment-transaction/")) {
		// Immediate action to hide default elements
		setTimeout(() => {
			// Hide Frappe's default add button immediately
			$(".list-view-container .list-header .btn-primary").hide();

			// Check for empty state immediately
			const $list_body = $(".list-view-container .list-body");
			if ($list_body.length && $list_body.find(".list-row").length === 0) {
				// Show custom empty state immediately
				const empty_state_html = `
                    <div class="custom-payment-transaction-empty-state">
                        <div class="empty-state-icon">
                            <i class="fa fa-exchange"></i>
                        </div>
                        <h3>${__("No Payment Transactions Yet")}</h3>
                        <p>${__("You haven't processed any payment transactions yet.")}</p>
                        <button class="btn btn-primary btn-create-transaction">
                            <i class="fa fa-plus"></i> ${__("Create Transaction")}
                        </button>
                    </div>
                `;
				$list_body.html(empty_state_html);

				// Bind button
				$(".btn-create-transaction").click(() => {
					frappe.new_doc("Payment Transaction");
				});
			}
		}, 100);
	}
});

// Monitor for route changes
$(document).on("route-change", function () {
	setTimeout(() => {
		if (window.location.pathname.includes("/payment-transaction/")) {
			console.log("Navigated to Payment Transaction list");

			// Re-apply our customizations
			const listview = window.payment_transaction_listview;
			if (listview && listview.inject_customizations) {
				listview.inject_customizations();
			} else {
				// Fallback: manually check and apply
				$(".list-view-container .list-header .btn-primary").hide();

				const $list_body = $(".list-view-container .list-body");
				if ($list_body.length && $list_body.find(".list-row").length === 0) {
					if ($list_body.find(".custom-payment-transaction-empty-state").length === 0) {
						const empty_state_html = `
                            <div class="custom-payment-transaction-empty-state">
                                <div class="empty-state-icon">
                                    <i class="fa fa-exchange"></i>
                                </div>
                                <h3>${__("No Payment Transactions Yet")}</h3>
                                <button class="btn btn-primary btn-create-transaction">
                                    <i class="fa fa-plus"></i> ${__("Create Transaction")}
                                </button>
                            </div>
                        `;
						$list_body.html(empty_state_html);

						$(".btn-create-transaction").click(() => {
							frappe.new_doc("Payment Transaction");
						});
					}
				}
			}
		}
	}, 500);
});
