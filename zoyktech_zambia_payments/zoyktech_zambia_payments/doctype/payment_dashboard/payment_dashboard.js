// payment_dashboard.js
frappe.ui.form.on("Payment Dashboard", {
	refresh: function (frm) {
		// Add standard ERPNext action buttons with clean styling
		frm.page.add_action_item(
			__("Refresh Dashboard"),
			function () {
				refresh_dashboard(frm);
			},
			"fa fa-refresh"
		);

		frm.page.add_action_item(
			__("Export to PDF"),
			function () {
				export_report(frm, "pdf");
			},
			"fa fa-file-pdf-o"
		);

		frm.page.add_action_item(
			__("Export to Excel"),
			function () {
				export_report(frm, "excel");
			},
			"fa fa-file-excel-o"
		);

		frm.page.add_action_item(
			__("Export to CSV"),
			function () {
				export_report(frm, "csv");
			},
			"fa fa-file-text-o"
		);

		frm.page.add_action_item(
			__("Email Report"),
			function () {
				email_report_dialog(frm);
			},
			"fa fa-envelope"
		);

		// Initialize dashboard
		init_dashboard(frm);
		load_dashboard_data(frm);
	},
});

function init_dashboard(frm) {
	const $wrapper = $(frm.fields_dict.dashboard_html.$wrapper);

	$wrapper.html(`
		<div class="payment-dashboard">
			<!-- Dashboard Header -->
			<div class="dashboard-header">
				<div class="header-top">
					<div>
						<h4>Payment Dashboard</h4>
						<small>Real-time payment analytics and insights</small>
					</div>
					<div class="last-updated">
						<div>Last Updated</div>
						<div id="last-updated">--</div>
					</div>
				</div>
				
				<div class="filters-section">
					<div class="filter-group">
						<label>Period</label>
						<select id="period-filter" class="form-control">
							<option value="7">Last 7 Days</option>
							<option value="30" selected>Last 30 Days</option>
							<option value="90">Last 90 Days</option>
							<option value="365">Last Year</option>
						</select>
					</div>
					
					<div class="filter-group">
						<label>Currency</label>
						<select id="currency-filter" class="form-control">
							<option value="ZMW" selected>ZMW</option>
							<option value="USD">USD</option>
						</select>
					</div>
					
					<div class="filter-actions">
						<button class="btn btn-default btn-sm" onclick="applyFilters()">
							<i class="fa fa-filter"></i> Apply Filters
						</button>
					</div>
				</div>
			</div>
			
			<!-- Summary Stats - Using CSS Grid -->
			<div class="stats-grid" id="summary-stats"></div>
			
			<!-- Charts Row 1 -->
			<div class="row chart-row">
				<div class="col-md-8">
					<div class="chart-card">
						<div class="chart-header">
							<h5><i class="fa fa-line-chart"></i> Daily Collections Trend</h5>
							<div class="chart-controls">
								<div class="btn-group chart-type-toggle">
									<button type="button" class="btn btn-xs btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
										<i class="fa fa-line-chart"></i> <span class="chart-type-label">Line</span> <span class="caret"></span>
									</button>
									<ul class="dropdown-menu">
										<li><a href="#" onclick="changeChartType('daily', 'line')"><i class="fa fa-line-chart"></i> Line Chart</a></li>
										<li><a href="#" onclick="changeChartType('daily', 'bar')"><i class="fa fa-bar-chart"></i> Bar Chart</a></li>
										<li><a href="#" onclick="changeChartType('daily', 'area')"><i class="fa fa-area-chart"></i> Area Chart</a></li>
										<li role="separator" class="divider"></li>
										<li><a href="#" onclick="changeChartType('daily', 'scatter')"><i class="fa fa-circle"></i> Scatter Chart</a></li>
										<li><a href="#" onclick="changeChartType('daily', 'radar')"><i class="fa fa-star"></i> Radar Chart</a></li>
									</ul>
								</div>
							</div>
						</div>
						<canvas id="daily-chart" height="250"></canvas>
						<div class="chart-legend" id="daily-chart-legend"></div>
					</div>
				</div>
				<div class="col-md-4">
					<div class="chart-card">
						<div class="chart-header">
							<h5><i class="fa fa-pie-chart"></i> Payment Methods</h5>
							<div class="chart-controls">
								<div class="btn-group chart-type-toggle">
									<button type="button" class="btn btn-xs btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
										<i class="fa fa-pie-chart"></i> <span class="chart-type-label">Doughnut</span> <span class="caret"></span>
									</button>
									<ul class="dropdown-menu">
										<li><a href="#" onclick="changeChartType('methods', 'doughnut')"><i class="fa fa-dashboard"></i> Doughnut Chart</a></li>
										<li><a href="#" onclick="changeChartType('methods', 'pie')"><i class="fa fa-pie-chart"></i> Pie Chart</a></li>
										<li><a href="#" onclick="changeChartType('methods', 'polarArea')"><i class="fa fa-bullseye"></i> Polar Area</a></li>
										<li role="separator" class="divider"></li>
										<li><a href="#" onclick="changeChartType('methods', 'bar')"><i class="fa fa-bar-chart"></i> Bar Chart</a></li>
									</ul>
								</div>
							</div>
						</div>
						<canvas id="methods-chart" height="250"></canvas>
						<div class="chart-legend" id="methods-chart-legend"></div>
					</div>
				</div>
			</div>
			
			<!-- Charts Row 2 -->
			<div class="row chart-row">
				<div class="col-md-6">
					<div class="chart-card">
						<div class="chart-header">
							<h5><i class="fa fa-bar-chart"></i> Monthly Collections</h5>
							<div class="chart-controls">
								<div class="btn-group chart-type-toggle">
									<button type="button" class="btn btn-xs btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
										<i class="fa fa-bar-chart"></i> <span class="chart-type-label">Bar</span> <span class="caret"></span>
									</button>
									<ul class="dropdown-menu">
										<li><a href="#" onclick="changeChartType('monthly', 'bar')"><i class="fa fa-bar-chart"></i> Bar Chart</a></li>
										<li><a href="#" onclick="changeChartType('monthly', 'line')"><i class="fa fa-line-chart"></i> Line Chart</a></li>
										<li><a href="#" onclick="changeChartType('monthly', 'area')"><i class="fa fa-area-chart"></i> Area Chart</a></li>
										<li role="separator" class="divider"></li>
										<li><a href="#" onclick="changeChartType('monthly', 'horizontalBar')"><i class="fa fa-ellipsis-h"></i> Horizontal Bar</a></li>
									</ul>
								</div>
							</div>
						</div>
						<canvas id="monthly-chart" height="220"></canvas>
						<div class="chart-legend" id="monthly-chart-legend"></div>
					</div>
				</div>
				<div class="col-md-6">
					<div class="chart-card">
						<div class="chart-header">
							<h5><i class="fa fa-chart-pie"></i> Status Distribution</h5>
							<div class="chart-controls">
								<div class="btn-group chart-type-toggle">
									<button type="button" class="btn btn-xs btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
										<i class="fa fa-pie-chart"></i> <span class="chart-type-label">Pie</span> <span class="caret"></span>
									</button>
									<ul class="dropdown-menu">
										<li><a href="#" onclick="changeChartType('status', 'pie')"><i class="fa fa-pie-chart"></i> Pie Chart</a></li>
										<li><a href="#" onclick="changeChartType('status', 'doughnut')"><i class="fa fa-dashboard"></i> Doughnut Chart</a></li>
										<li><a href="#" onclick="changeChartType('status', 'bar')"><i class="fa fa-bar-chart"></i> Bar Chart</a></li>
										<li role="separator" class="divider"></li>
										<li><a href="#" onclick="changeChartType('status', 'polarArea')"><i class="fa fa-bullseye"></i> Polar Area</a></li>
									</ul>
								</div>
							</div>
						</div>
						<canvas id="status-chart" height="220"></canvas>
						<div class="chart-legend" id="status-chart-legend"></div>
					</div>
				</div>
			</div>
			
			<!-- Data Tables -->
			<div class="row table-row">
				<div class="col-md-6">
					<div class="table-card">
						<div class="table-header">
							<h5><i class="fa fa-history"></i> Recent Transactions</h5>
							<a href="/app/payment-transaction" class="btn btn-xs btn-default">
								<i class="fa fa-external-link"></i> View All
							</a>
						</div>
						<div class="table-responsive">
							<table class="table table-bordered" id="recent-transactions-table">
								<thead>
									<tr>
										<th style="width: 25%;">Date</th>
										<th style="width: 30%;">Reference</th>
										<th style="width: 25%;">Amount</th>
										<th style="width: 20%;">Status</th>
									</tr>
								</thead>
								<tbody id="transactions-table"></tbody>
							</table>
							<div id="transactions-empty" class="empty-state" style="display: none;">
								<i class="fa fa-database"></i>
								<h4>No Recent Transactions</h4>
								<p>No payment transactions found for the selected period</p>
							</div>
						</div>
					</div>
				</div>
				<div class="col-md-6">
					<div class="table-card">
						<div class="table-header">
							<h5><i class="fa fa-users"></i> Top Customers</h5>
						</div>
						<div class="table-responsive">
							<table class="table table-bordered" id="top-customers-table">
								<thead>
									<tr>
										<th style="width: 50%;">Customer</th>
										<th style="width: 25%;">Transactions</th>
										<th style="width: 25%;">Total</th>
									</tr>
								</thead>
								<tbody id="customers-table"></tbody>
							</table>
							<div id="customers-empty" class="empty-state" style="display: none;">
								<i class="fa fa-users"></i>
								<h4>No Customer Data</h4>
								<p>No customer payment data found for the selected period</p>
							</div>
						</div>
					</div>
				</div>
			</div>
			
			<style>
				.payment-dashboard {
					padding: 20px;
					min-height: 100vh;
					background-color: white;
				}
				
				.dashboard-header {
					background: white;
					border: 1px solid #e0e0e0;
					border-radius: 4px;
					padding: 20px;
					margin-bottom: 20px;
					box-shadow: 0 1px 3px rgba(0,0,0,0.08);
				}
				
				.header-top {
					display: flex;
					justify-content: space-between;
					align-items: flex-start;
					margin-bottom: 20px;
				}
				
				.header-top h4 {
					margin: 0 0 5px 0;
					color: #1a1a1a;
					font-size: 20px;
					font-weight: 600;
				}
				
				.header-top small {
					color: #666;
					font-size: 13px;
				}
				
				.last-updated {
					text-align: right;
					background: white;
					padding: 8px 12px;
					border-radius: 4px;
					border: 1px solid #e0e0e0;
				}
				
				.last-updated > div:first-child {
					font-size: 11px;
					color: #666;
					margin-bottom: 4px;
				}
				
				#last-updated {
					font-weight: 600;
					color: #1a1a1a;
					font-size: 13px;
				}
				
				.filters-section {
					display: flex;
					gap: 15px;
					align-items: flex-end;
					flex-wrap: wrap;
					padding-top: 15px;
					border-top: 1px solid #f0f0f0;
				}
				
				.filter-group {
					flex: 1;
					min-width: 200px;
				}
				
				.filter-group label {
					display: block;
					margin-bottom: 5px;
					color: #1a1a1a;
					font-weight: 500;
					font-size: 13px;
				}
				
				.form-control {
					border: 1px solid #d0d0d0;
					border-radius: 4px;
					padding: 8px 12px;
					height: 38px;
					font-size: 13px;
					background-color: white;
					transition: border-color 0.15s ease-in-out;
				}
				
				.form-control:focus {
					border-color: #1a1a1a;
					box-shadow: 0 0 0 1px rgba(26, 26, 26, 0.1);
					outline: none;
				}
				
				.filter-actions .btn {
					background-color: white;
					border: 1px solid #d0d0d0;
					color: #1a1a1a;
					padding: 8px 16px;
					height: 38px;
					border-radius: 4px;
					font-weight: 500;
					font-size: 13px;
					transition: all 0.15s ease-in-out;
				}
				
				.filter-actions .btn:hover {
					background-color: #f8f9fa;
					border-color: #1a1a1a;
				}
				
				.chart-row {
					margin-bottom: 20px;
				}
				
				.chart-card {
					background: white;
					border: 1px solid #e0e0e0;
					border-radius: 4px;
					padding: 20px;
					height: 100%;
					box-shadow: 0 1px 3px rgba(0,0,0,0.08);
				}
				
				.chart-header {
					display: flex;
					justify-content: space-between;
					align-items: center;
					margin: 0 0 20px 0;
					color: #1a1a1a;
					border-bottom: 1px solid #f0f0f0;
					padding-bottom: 12px;
				}
				
				.chart-header h5 {
					margin: 0;
					display: flex;
					align-items: center;
					gap: 8px;
					font-size: 15px;
					font-weight: 600;
				}
				
				.chart-header h5 i {
					color: #666;
				}
				
				.chart-controls {
					display: flex;
					align-items: center;
					gap: 10px;
				}
				
				.chart-type-toggle .btn {
					background-color: white;
					border: 1px solid #d0d0d0;
					color: #1a1a1a;
					padding: 4px 10px;
					font-size: 11px;
					border-radius: 3px;
					transition: all 0.15s ease-in-out;
				}
				
				.chart-type-toggle .btn:hover {
					background-color: #f8f9fa;
					border-color: #1a1a1a;
				}
				
				.chart-type-toggle .dropdown-menu {
					min-width: 160px;
					border: 1px solid #e0e0e0;
					border-radius: 4px;
					box-shadow: 0 2px 8px rgba(0,0,0,0.1);
					margin-top: 5px;
				}
				
				.chart-type-toggle .dropdown-menu li a {
					padding: 6px 12px;
					font-size: 12px;
					color: #1a1a1a;
					display: flex;
					align-items: center;
					gap: 8px;
					transition: all 0.15s ease-in-out;
				}
				
				.chart-type-toggle .dropdown-menu li a:hover {
					background-color: #f8f9fa;
					color: #1a1a1a;
				}
				
				.chart-type-toggle .dropdown-menu li a i {
					width: 16px;
					text-align: center;
				}
				
				.chart-legend {
					margin-top: 15px;
					padding: 10px;
					background: #f9f9f9;
					border-radius: 4px;
					font-size: 12px;
					color: #666;
					border: 1px solid #f0f0f0;
				}
				
				.table-row {
					margin-bottom: 20px;
				}
				
				.table-card {
					background: white;
					border: 1px solid #e0e0e0;
					border-radius: 4px;
					height: 100%;
					box-shadow: 0 1px 3px rgba(0,0,0,0.08);
				}
				
				.table-header {
					padding: 16px 20px;
					border-bottom: 1px solid #f0f0f0;
					display: flex;
					justify-content: space-between;
					align-items: center;
					background-color: white;
				}
				
				.table-header h5 {
					margin: 0;
					color: #1a1a1a;
					display: flex;
					align-items: center;
					gap: 8px;
					font-size: 15px;
					font-weight: 600;
				}
				
				.table-header h5 i {
					color: #666;
				}
				
				.table-header .btn {
					background-color: white;
					border: 1px solid #d0d0d0;
					color: #1a1a1a;
					padding: 5px 10px;
					font-size: 11px;
					border-radius: 3px;
					transition: all 0.15s ease-in-out;
				}
				
				.table-header .btn:hover {
					background-color: #f8f9fa;
					border-color: #1a1a1a;
				}
				
				.table-responsive {
					overflow-x: auto;
					padding: 16px 20px;
				}
				
				#recent-transactions-table,
				#top-customers-table {
					margin: 0;
					border-color: #f0f0f0;
				}
				
				#recent-transactions-table th,
				#top-customers-table th {
					background: white;
					font-weight: 600;
					color: #1a1a1a;
					border-bottom: 2px solid #f0f0f0;
					padding: 10px 12px;
					font-size: 12px;
				}
				
				#recent-transactions-table td,
				#top-customers-table td {
					vertical-align: middle;
					border-bottom: 1px solid #f8f8f8;
					padding: 10px 12px;
					font-size: 12px;
				}
				
				.stats-grid {
					display: grid;
					grid-template-columns: repeat(3, 1fr);
					gap: 15px;
					margin-bottom: 20px;
				}
				
				.stat-card {
					background: white;
					border: 1px solid #e0e0e0;
					border-radius: 4px;
					padding: 20px;
					text-align: center;
					height: 100%;
					transition: transform 0.2s ease-in-out;
					box-shadow: 0 1px 3px rgba(0,0,0,0.08);
				}
				
				.stat-card:hover {
					transform: translateY(-1px);
					box-shadow: 0 2px 5px rgba(0,0,0,0.1);
				}
				
				.stat-label {
					margin-bottom: 10px;
					color: #666;
					font-size: 12px;
					text-transform: uppercase;
					letter-spacing: 0.5px;
					display: flex;
					align-items: center;
					justify-content: center;
					gap: 6px;
					font-weight: 500;
				}
				
				.stat-label i {
					color: #666;
					font-size: 13px;
				}
				
				.stat-value {
					font-size: 24px;
					font-weight: 600;
					color: #1a1a1a;
					margin-bottom: 6px;
					line-height: 1.2;
				}
				
				.stat-footer {
					color: #666;
					font-size: 11px;
					padding-top: 6px;
					border-top: 1px solid #f8f8f8;
					margin-top: 10px;
				}
				
				.empty-state {
					padding: 40px 20px;
					text-align: center;
					color: #666;
					background-color: white;
					border-radius: 4px;
					border: 1px dashed #e0e0e0;
					margin: 15px;
				}
				
				.empty-state i {
					font-size: 48px;
					margin-bottom: 15px;
					color: #ccc;
				}
				
				.empty-state h4 {
					color: #1a1a1a;
					margin-bottom: 10px;
					font-size: 16px;
					font-weight: 600;
				}
				
				.empty-state p {
					margin-bottom: 15px;
					max-width: 400px;
					margin-left: auto;
					margin-right: auto;
					line-height: 1.5;
					font-size: 13px;
				}
				
				.label {
					padding: 3px 8px;
					border-radius: 3px;
					font-size: 11px;
					font-weight: 500;
					display: inline-block;
				}
				
				.label-success {
					background-color: #e8f5e9;
					color: #2e7d32;
					border: 1px solid #c8e6c9;
				}
				
				.label-warning {
					background-color: #fff8e1;
					color: #ff8f00;
					border: 1px solid #ffecb3;
				}
				
				.label-danger {
					background-color: #ffebee;
					color: #c62828;
					border: 1px solid #ffcdd2;
				}
				
				.label-default {
					background-color: #f5f5f5;
					color: #424242;
					border: 1px solid #e0e0e0;
				}
				
				.label-info {
					background-color: #e3f2fd;
					color: #1565c0;
					border: 1px solid #bbdefb;
				}
				
				@media (max-width: 992px) {
					.stats-grid {
						grid-template-columns: repeat(2, 1fr);
						gap: 12px;
					}
				}
				
				@media (max-width: 768px) {
					.payment-dashboard {
						padding: 15px;
					}
					
					.stats-grid {
						grid-template-columns: 1fr;
						gap: 10px;
					}
					
					.filters-section {
						flex-direction: column;
						gap: 12px;
					}
					
					.filter-group {
						width: 100%;
						min-width: unset;
					}
					
					.header-top {
						flex-direction: column;
						align-items: flex-start;
						gap: 12px;
					}
					
					.last-updated {
						text-align: left;
						width: 100%;
					}
					
					.chart-card,
					.table-card,
					.dashboard-header {
						padding: 16px;
					}
					
					.stat-card {
						padding: 16px;
					}
					
					.stat-value {
						font-size: 22px;
					}
					
					.chart-header {
						flex-direction: column;
						align-items: flex-start;
						gap: 10px;
					}
					
					.chart-controls {
						align-self: flex-end;
					}
				}
				
				@media (max-width: 576px) {
					.chart-row .col-md-8,
					.chart-row .col-md-4,
					.chart-row .col-md-6,
					.table-row .col-md-6 {
						margin-bottom: 12px;
					}
					
					.chart-controls {
						align-self: stretch;
					}
					
					.chart-type-toggle {
						width: 100%;
					}
					
					.chart-type-toggle .btn {
						width: 100%;
						justify-content: space-between;
					}
				}
			</style>
		</div>
	`);
}

// Global variables to store chart data and configuration
window.chartData = {
	daily: null,
	methods: null,
	monthly: null,
	status: null,
};

window.chartTypes = {
	daily: "line",
	methods: "doughnut",
	monthly: "bar",
	status: "pie",
};

window.chartIcons = {
	line: "fa-line-chart",
	bar: "fa-bar-chart",
	area: "fa-area-chart",
	scatter: "fa-circle",
	radar: "fa-star",
	doughnut: "fa-dashboard",
	pie: "fa-pie-chart",
	polarArea: "fa-bullseye",
	horizontalBar: "fa-ellipsis-h",
};

window.chartLabels = {
	line: "Line",
	bar: "Bar",
	area: "Area",
	scatter: "Scatter",
	radar: "Radar",
	doughnut: "Doughnut",
	pie: "Pie",
	polarArea: "Polar Area",
	horizontalBar: "Horizontal Bar",
};

function changeChartType(chartId, chartType) {
	window.chartTypes[chartId] = chartType;

	// Update the button label
	const button = $(`.chart-type-toggle:has(a[onclick*="${chartId}"])`).find(".btn");
	const iconClass = window.chartIcons[chartType];
	const label = window.chartLabels[chartType];

	button
		.find("i")
		.removeClass()
		.addClass("fa " + iconClass);
	button.find(".chart-type-label").text(label);

	// Re-render the chart
	switch (chartId) {
		case "daily":
			if (window.chartData.daily) {
				render_chart("daily", window.chartData.daily, chartType);
			}
			break;
		case "methods":
			if (window.chartData.methods) {
				render_chart("methods", window.chartData.methods, chartType);
			}
			break;
		case "monthly":
			if (window.chartData.monthly) {
				render_chart("monthly", window.chartData.monthly, chartType);
			}
			break;
		case "status":
			if (window.chartData.status) {
				render_chart("status", window.chartData.status, chartType);
			}
			break;
	}

	return false; // Prevent default link behavior
}

function render_chart(chartId, data, chartType = null) {
	if (!chartType) {
		chartType = window.chartTypes[chartId];
	}

	// Store the data for later re-rendering
	window.chartData[chartId] = data;

	const canvasId = `${chartId}-chart`;
	const ctx = document.getElementById(canvasId)?.getContext("2d");

	if (!ctx) return;

	// Destroy existing chart if it exists
	if (window[`${chartId}Chart`]) {
		window[`${chartId}Chart`].destroy();
	}

	// Handle empty data
	if (!data || (Array.isArray(data) && data.length === 0)) {
		ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		ctx.fillStyle = "#666";
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";
		ctx.font = "13px Arial";
		ctx.fillText("No data available", ctx.canvas.width / 2, ctx.canvas.height / 2);
		$(`#${canvasId}-legend`).empty();
		return;
	}

	// Render based on chart type
	switch (chartId) {
		case "daily":
			render_daily_chart(data, chartType);
			break;
		case "methods":
			render_methods_chart(data, chartType);
			break;
		case "monthly":
			render_monthly_chart(data, chartType);
			break;
		case "status":
			render_status_chart(data, chartType);
			break;
	}
}

function load_dashboard_data(frm, showLoader = true) {
	const days = $("#period-filter").val() || 30;
	const currency = $("#currency-filter").val() || "ZMW";

	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.get_dashboard_data",
		args: { days: parseInt(days), currency: currency },
		callback: function (r) {
			if (r.message && !r.message.error) {
				render_dashboard(r.message, currency);
				$("#last-updated").text(frappe.datetime.now_datetime());
			} else {
				frappe.msgprint({
					title: __("Error"),
					indicator: "red",
					message: r.message?.error || __("Failed to load dashboard"),
				});
			}
		},
		error: function () {
			frappe.msgprint(__("Network error. Please try again."));
		},
	});
}

// ===================== HELPER FUNCTIONS =====================

// Helper function to safely format data
function safeFormat(value, defaultValue = "N/A") {
	if (value === null || value === undefined || value === "") {
		return defaultValue;
	}
	return value;
}

// Update render_dashboard to handle missing data
function render_dashboard(data, currency) {
	try {
		// Check if data is valid
		if (!data || data.error) {
			showErrorState(data?.error || "Failed to load dashboard data");
			return;
		}

		// Render each section with fallbacks
		render_summary_stats(data.summary_stats || {}, currency);

		// Store and render charts with current chart types
		window.chartData.daily = data.daily_collections || {};
		window.chartData.methods = data.payment_methods_breakdown || [];
		window.chartData.monthly = data.monthly_collections || {};
		window.chartData.status = data.status_distribution || [];

		render_chart("daily", window.chartData.daily);
		render_chart("methods", window.chartData.methods);
		render_chart("monthly", window.chartData.monthly);
		render_chart("status", window.chartData.status);

		render_transactions_table(data.recent_transactions || []);
		render_customers_table(data.top_customers || [], currency);

		// Update last updated timestamp
		$("#last-updated").text(frappe.datetime.now_datetime());
	} catch (error) {
		console.error("Error rendering dashboard:", error);
		showErrorState("Error rendering dashboard");
	}
}

function showErrorState(message) {
	// Clear existing content
	$("#summary-stats").html(`
        <div class="col-md-12">
            <div class="alert alert-danger">
                <h4><i class="fa fa-exclamation-triangle"></i> Error Loading Dashboard</h4>
				<p>${message}</p>
				<button class="btn btn-default btn-sm" onclick="location.reload()">
					<i class="fa fa-refresh"></i> Retry
				</button>
			</div>
		</div>
	`);

	// Show empty states for all sections
	$("#transactions-empty").show();
	$("#customers-empty").show();

	// Clear charts
	clearAllCharts();
}

function clearAllCharts() {
	const chartIds = ["daily-chart", "methods-chart", "monthly-chart", "status-chart"];
	chartIds.forEach((id) => {
		const ctx = document.getElementById(id)?.getContext("2d");
		if (ctx) {
			ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
			ctx.fillStyle = "#666";
			ctx.textAlign = "center";
			ctx.textBaseline = "middle";
			ctx.font = "13px Arial";
			ctx.fillText("No data available", ctx.canvas.width / 2, ctx.canvas.height / 2);
		}
		$(`#${id}-legend`).empty();
	});
}

function render_summary_stats(stats, currency) {
	const html = `
		<div class="stat-card">
			<div class="stat-label"><i class="fa fa-money"></i> Total Collections</div>
			<div class="stat-value">${fmt_currency(stats.total_collections, currency)}</div>
			<div class="stat-footer">Net: ${fmt_currency(stats.net_collections, currency)}</div>
		</div>
		
		<div class="stat-card">
			<div class="stat-label"><i class="fa fa-check-circle"></i> Successful</div>
			<div class="stat-value">${safeFormat(stats.successful_payments, 0).toLocaleString()}</div>
			<div class="stat-footer">${safeFormat(stats.conversion_rate, 0)}% conversion rate</div>
		</div>
		
		<div class="stat-card">
			<div class="stat-label"><i class="fa fa-clock-o"></i> Pending</div>
			<div class="stat-value">${safeFormat(stats.pending_payments, 0).toLocaleString()}</div>
			<div class="stat-footer">Awaiting processing</div>
		</div>
		
		<div class="stat-card">
			<div class="stat-label"><i class="fa fa-calculator"></i> Avg Transaction</div>
			<div class="stat-value">${fmt_currency(safeFormat(stats.avg_transaction_value, 0), currency)}</div>
			<div class="stat-footer">${safeFormat(stats.yoy_growth, 0)}% YoY growth</div>
		</div>
		
		<div class="stat-card">
			<div class="stat-label"><i class="fa fa-times-circle"></i> Failed</div>
			<div class="stat-value">${safeFormat(stats.failed_payments, 0).toLocaleString()}</div>
			<div class="stat-footer">Requires attention</div>
		</div>
		
		<div class="stat-card">
			<div class="stat-label"><i class="fa fa-exchange"></i> Total</div>
			<div class="stat-value">${safeFormat(stats.total_transactions, 0).toLocaleString()}</div>
			<div class="stat-footer">All payments</div>
		</div>
	`;

	$("#summary-stats").html(html);
}

function render_daily_chart(data, chartType = "line") {
	const ctx = document.getElementById("daily-chart").getContext("2d");
	const legendContainer = $("#daily-chart-legend");

	if (window.dailyChart) window.dailyChart.destroy();

	if (
		data &&
		data.labels &&
		data.labels.length > 0 &&
		data.datasets &&
		data.datasets.length > 0
	) {
		const datasets = data.datasets.map((dataset, index) => {
			const colors = [
				{ border: "#1a1a1a", bg: "rgba(26, 26, 26, 0.1)" },
				{ border: "#666", bg: "rgba(102, 102, 102, 0.1)" },
				{ border: "#999", bg: "rgba(153, 153, 153, 0.1)" },
			];

			const color = colors[index] || colors[0];

			return {
				...dataset,
				borderColor: color.border,
				backgroundColor:
					chartType === "area" || chartType === "radar" ? color.bg : "transparent",
				fill: chartType === "area" || chartType === "radar",
				borderWidth: 2,
				tension:
					chartType === "line" || chartType === "area" || chartType === "radar"
						? 0.3
						: 0,
				pointRadius: chartType === "scatter" ? 5 : 3,
				pointHoverRadius: 6,
			};
		});

		const options = {
			responsive: true,
			maintainAspectRatio: false,
			interaction: { mode: "index", intersect: false },
			scales:
				chartType === "horizontalBar"
					? {
							x: {
								beginAtZero: true,
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
							y: {
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
					  }
					: {
							y: {
								type: "linear",
								display: true,
								position: "left",
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
								beginAtZero: true,
							},
							x: {
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
					  },
			plugins: {
				legend: {
					display: false, // We'll use custom legend
				},
			},
		};

		// Add secondary axis for line/area charts
		if ((chartType === "line" || chartType === "area") && datasets.length > 1) {
			options.scales.y1 = {
				type: "linear",
				display: true,
				position: "right",
				grid: { drawOnChartArea: false },
				ticks: { color: "#666" },
				beginAtZero: true,
			};
			datasets[1].yAxisID = "y1";
		}

		window.dailyChart = new Chart(ctx, {
			type: chartType,
			data: {
				labels: data.labels,
				datasets: datasets,
			},
			options: options,
		});

		// Update custom legend
		updateLegend(legendContainer, data.datasets, "daily");
	} else {
		// Show empty state for chart
		ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		ctx.fillStyle = "#666";
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";
		ctx.font = "13px Arial";
		ctx.fillText(
			"No data available for selected period",
			ctx.canvas.width / 2,
			ctx.canvas.height / 2
		);
		legendContainer.empty();
	}
}

function render_methods_chart(data, chartType = "doughnut") {
	const ctx = document.getElementById("methods-chart").getContext("2d");
	const legendContainer = $("#methods-chart-legend");

	if (window.methodsChart) window.methodsChart.destroy();

	if (data && data.length > 0) {
		const colors = ["#1a1a1a", "#333", "#555", "#777", "#999", "#bbb", "#ddd", "#eee"];

		const chartData = {
			labels: data.map((m) => safeFormat(m.method, "Unknown")),
			datasets: [
				{
					data: data.map((m) => safeFormat(m.total, 0)),
					backgroundColor: colors,
					borderWidth: 2,
					borderColor: "#fff",
				},
			],
		};

		const options = {
			responsive: true,
			maintainAspectRatio: false,
			cutout: chartType === "doughnut" ? "65%" : 0,
			plugins: {
				legend: {
					display: false, // We'll use custom legend
				},
			},
		};

		// Special options for polar area
		if (chartType === "polarArea") {
			options.scales = {
				r: {
					ticks: {
						display: false,
					},
				},
			};
		}

		window.methodsChart = new Chart(ctx, {
			type: chartType,
			data: chartData,
			options: options,
		});

		// Update custom legend
		updateLegend(legendContainer, chartData.datasets, "methods", chartData.labels);
	} else {
		// Show empty state for chart
		ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		ctx.fillStyle = "#666";
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";
		ctx.font = "13px Arial";
		ctx.fillText("No payment method data", ctx.canvas.width / 2, ctx.canvas.height / 2);
		legendContainer.empty();
	}
}

function render_monthly_chart(data, chartType = "bar") {
	const ctx = document.getElementById("monthly-chart").getContext("2d");
	const legendContainer = $("#monthly-chart-legend");

	if (window.monthlyChart) window.monthlyChart.destroy();

	if (
		data &&
		data.labels &&
		data.labels.length > 0 &&
		data.datasets &&
		data.datasets.length > 0
	) {
		const datasets = data.datasets.map((dataset, index) => {
			const colors = [
				{
					border: "#1a1a1a",
					bg:
						chartType === "horizontalBar"
							? "rgba(26, 26, 26, 0.8)"
							: "rgba(26, 26, 26, 0.8)",
				},
				{ border: "#666", bg: "rgba(102, 102, 102, 0.8)" },
				{ border: "#999", bg: "rgba(153, 153, 153, 0.8)" },
			];

			const color = colors[index] || colors[0];

			return {
				...dataset,
				backgroundColor: color.bg,
				borderColor: color.border,
				borderWidth: 1,
				borderRadius: chartType === "bar" || chartType === "horizontalBar" ? 3 : 0,
				fill: chartType === "area",
			};
		});

		const options = {
			responsive: true,
			maintainAspectRatio: false,
			scales:
				chartType === "horizontalBar"
					? {
							x: {
								beginAtZero: true,
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
							y: {
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
					  }
					: {
							y: {
								beginAtZero: true,
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
							x: {
								grid: { color: "#f5f5f5" },
								ticks: { color: "#666" },
							},
					  },
			plugins: {
				legend: {
					display: false, // We'll use custom legend
				},
			},
		};

		window.monthlyChart = new Chart(ctx, {
			type: chartType,
			data: {
				labels: data.labels,
				datasets: datasets,
			},
			options: options,
		});

		// Update custom legend
		updateLegend(legendContainer, data.datasets, "monthly");
	} else {
		// Show empty state for chart
		ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		ctx.fillStyle = "#666";
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";
		ctx.font = "13px Arial";
		ctx.fillText("No monthly collection data", ctx.canvas.width / 2, ctx.canvas.height / 2);
		legendContainer.empty();
	}
}

function render_status_chart(data, chartType = "pie") {
	const ctx = document.getElementById("status-chart").getContext("2d");
	const legendContainer = $("#status-chart-legend");

	if (window.statusChart) window.statusChart.destroy();

	if (data && data.length > 0) {
		const colors = {
			Completed: "#1a1a1a",
			Pending: "#666",
			Failed: "#999",
			Refunded: "#bbb",
			Cancelled: "#ddd",
		};

		const chartData = {
			labels: data.map((s) => safeFormat(s.status, "Unknown")),
			datasets: [
				{
					data: data.map((s) => safeFormat(s.count, 0)),
					backgroundColor: data.map(
						(s) => colors[safeFormat(s.status, "Unknown")] || "#ddd"
					),
					borderWidth: 2,
					borderColor: "#fff",
				},
			],
		};

		const options = {
			responsive: true,
			maintainAspectRatio: false,
			cutout: chartType === "doughnut" ? "65%" : 0,
			plugins: {
				legend: {
					display: false, // We'll use custom legend
				},
			},
		};

		// Special options for polar area
		if (chartType === "polarArea") {
			options.scales = {
				r: {
					ticks: {
						display: false,
					},
				},
			};
		}

		window.statusChart = new Chart(ctx, {
			type: chartType,
			data: chartData,
			options: options,
		});

		// Update custom legend
		updateLegend(legendContainer, chartData.datasets, "status", chartData.labels);
	} else {
		// Show empty state for chart
		ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
		ctx.fillStyle = "#666";
		ctx.textAlign = "center";
		ctx.textBaseline = "middle";
		ctx.font = "13px Arial";
		ctx.fillText("No status distribution data", ctx.canvas.width / 2, ctx.canvas.height / 2);
		legendContainer.empty();
	}
}

function updateLegend(container, datasets, chartId, labels = null) {
	container.empty();

	if (!datasets || datasets.length === 0) return;

	const legendItems = [];

	datasets.forEach((dataset, datasetIndex) => {
		if (labels) {
			// For pie/doughnut charts with single dataset
			dataset.backgroundColor.forEach((color, index) => {
				legendItems.push({
					color: color,
					label: labels[index] || `Item ${index + 1}`,
					value: dataset.data[index],
				});
			});
		} else {
			// For multi-dataset charts
			const color = dataset.borderColor || dataset.backgroundColor || "#1a1a1a";
			legendItems.push({
				color: color,
				label: dataset.label || `Dataset ${datasetIndex + 1}`,
				value: null,
			});
		}
	});

	if (legendItems.length > 0) {
		const legendHtml = legendItems
			.map(
				(item) => `
			<div class="legend-item" style="display: inline-flex; align-items: center; margin-right: 15px; margin-bottom: 5px;">
				<span class="legend-color" style="display: inline-block; width: 12px; height: 12px; background-color: ${
					item.color
				}; border-radius: 2px; margin-right: 6px; border: 1px solid #e0e0e0;"></span>
				<span class="legend-label" style="font-size: 11px; color: #666;">${item.label}</span>
				${
					item.value !== null
						? `<span class="legend-value" style="margin-left: 4px; font-size: 11px; color: #1a1a1a; font-weight: 500;">(${item.value})</span>`
						: ""
				}
			</div>
		`
			)
			.join("");

		container.html(`<div style="display: flex; flex-wrap: wrap;">${legendHtml}</div>`);
	}
}

// Update render_transactions_table to handle missing data
function render_transactions_table(transactions) {
	const tbody = $("#transactions-table");
	const emptyState = $("#transactions-empty");

	tbody.empty();

	if (transactions && transactions.length > 0) {
		emptyState.hide();
		tbody.show();
		transactions.slice(0, 6).forEach((txn) => {
			const status_classes = {
				Completed: "label-success",
				Pending: "label-warning",
				Failed: "label-danger",
				Refunded: "label-info",
			};

			tbody.append(`
				<tr>
					<td><small>${safeFormat(txn.formatted_date, "N/A")}</small></td>
					<td><code style="font-size: 11px; padding: 2px 6px; border-radius: 2px; border: 1px solid #e0e0e0;">${safeFormat(
						txn.reference_id,
						"N/A"
					)}</code></td>
					<td style="font-weight: 600;">${fmt_currency(
						safeFormat(txn.amount, 0),
						safeFormat(txn.currency, "ZMW")
					)}</td>
					<td><span class="label ${
						status_classes[safeFormat(txn.status, "Unknown")] || "label-default"
					}">${safeFormat(txn.status, "Unknown")}</span></td>
				</tr>
			`);
		});
	} else {
		tbody.hide();
		emptyState.show();
	}
}

// Update render_customers_table to handle missing data
function render_customers_table(customers, currency) {
	const tbody = $("#customers-table");
	const emptyState = $("#customers-empty");

	tbody.empty();

	if (customers && customers.length > 0) {
		emptyState.hide();
		tbody.show();
		customers.slice(0, 6).forEach((c) => {
			tbody.append(`
				<tr>
					<td style="font-weight: 600;">${safeFormat(c.customer, "Anonymous")}</td>
					<td><span class="label label-default">${safeFormat(c.transaction_count, 0)}</span></td>
					<td style="font-weight: 600;">${fmt_currency(safeFormat(c.total_amount, 0), currency)}</td>
				</tr>
			`);
		});
	} else {
		tbody.hide();
		emptyState.show();
	}
}

function refresh_dashboard(frm) {
	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.refresh_dashboard_cache",
		freeze: true,
		freeze_message: __("Refreshing..."),
		callback: function (r) {
			if (r.message?.success) {
				frappe.show_alert({ message: __("Dashboard refreshed"), indicator: "green" });
				load_dashboard_data(frm);
			}
		},
	});
}

function export_report(frm, format) {
	const days = $("#period-filter").val() || 30;

	frappe.call({
		method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.export_dashboard_report",
		args: {
			days: days,
			report_type: "all data",
			format_type: format,
		},
		freeze: true,
		freeze_message: __("Generating report..."),
		callback: function (r) {
			if (r.message?.success) {
				download_file(r.message.data, r.message.filename, r.message.mime_type);
				frappe.show_alert({ message: __("Report exported"), indicator: "green" });
			}
		},
	});
}

function email_report_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __("Email Report"),
		fields: [
			{
				fieldname: "email",
				fieldtype: "Data",
				label: __("Email Address"),
				reqd: 1,
				options: "Email",
			},
			{
				fieldname: "days",
				fieldtype: "Int",
				label: __("Days"),
				default: 30,
			},
		],
		primary_action_label: __("Send"),
		primary_action: (values) => {
			frappe.call({
				method: "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.send_dashboard_email",
				args: {
					email: values.email,
					days: values.days,
					report_type: "summary",
				},
				freeze: true,
				callback: function (r) {
					if (r.message?.success) {
						frappe.show_alert({ message: r.message.message, indicator: "green" });
						d.hide();
					}
				},
			});
		},
	});

	d.show();
}

function download_file(data, filename, mimeType) {
	const blob = new Blob([data], { type: mimeType });
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
	window.URL.revokeObjectURL(url);
}

function fmt_currency(amount, currency) {
	const formatted = parseFloat(amount || 0).toLocaleString("en-US", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2,
	});
	return `${currency} ${formatted}`;
}

function applyFilters() {
	const frm = cur_frm;
	load_dashboard_data(frm);
}

// Load Chart.js if needed
if (typeof Chart === "undefined") {
	frappe.require("assets/frappe/js/lib/chart.min.js");
}
