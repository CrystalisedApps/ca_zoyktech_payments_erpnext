# hooks.py

from . import __version__ as app_version

app_name = "zoyktech_zambia_payments"
app_title = "Zoyktech Zambia Payments"
app_publisher = "Marty Muhanga"
app_description = "Complete Payment Gateway Integration for Zambia with ERPNext."
app_icon = "octicon octicon-credit-card"
app_color = "green"
app_email = "marty@crystalisedapps.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "zoyktech_zambia_payments",
# 		"logo": "/assets/zoyktech_zambia_payments/logo.png",
# 		"title": "Zoyktech Zambia Payments",
# 		"route": "/zoyktech_zambia_payments",
# 		"has_permission": "zoyktech_zambia_payments.api.permission.has_app_permission"
# 	}
# ]

doctype = ["Payment Dashboard", "Payment Transaction"]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
	"/assets/zoyktech_zambia_payments/css/payment_buttons.css",
	"/assets/zoyktech_zambia_payments/css/payment_forms.css",
	# "/assets/zoyktech_zambia_payments/css/payment_dashboard.css"
]
app_include_js = [
	"/assets/zoyktech_zambia_payments/js/payment_integration.js",
	"/assets/zoyktech_zambia_payments/js/payment_buttons.js",
]

# include js, css files in header of web template
web_include_css = ["/assets/zoyktech_zambia_payments/css/payment_forms.css"]
web_include_js = ["/assets/zoyktech_zambia_payments/js/webhook_handler.js"]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "zoyktech_zambia_payments/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
page_js = {"point-of-sale": "public/js/pos_payment_integration.js"}

# include js in doctype views
doctype_js = {
	"Sales Invoice": "public/js/sales_invoice_payments.js",
	"Purchase Invoice": "public/js/purchase_invoice_payments.js",
	"Sales Order": "public/js/sales_order_payments.js",
	"Payment Entry": "public/js/payment_entry_enhancements.js",
	"Payment Dashboard": "public/js/payment_dashboard.js",
}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "zoyktech_zambia_payments/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "zoyktech_zambia_payments.utils.jinja_methods",
# 	"filters": "zoyktech_zambia_payments.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "zoyktech_zambia_payments.install.before_install"
after_install = "zoyktech_zambia_payments.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "zoyktech_zambia_payments.uninstall.before_uninstall"
# after_uninstall = "zoyktech_zambia_payments.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument
dependencies = ["erpnext"]

# before_app_install = "zoyktech_zambia_payments.utils.before_app_install"
# after_app_install = "zoyktech_zambia_payments.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "zoyktech_zambia_payments.utils.before_app_uninstall"
# after_app_uninstall = "zoyktech_zambia_payments.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "zoyktech_zambia_payments.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Payment Entry": "zoyktech_zambia_payments.zoyktech_zambia_payments.overrides.payment_entry.CustomPaymentEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Sales Invoice": {
		"on_submit": "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.invoice_handlers.create_payment_link_on_submit",
		"on_payment_authorized": "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.invoice_handlers.handle_payment_authorization",
	},
	"Payment Entry": {
		"on_submit": "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.payment_handlers.update_payment_gateway_status",
		"on_cancel": "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.payment_handlers.handle_payment_cancellation",
	},
	"Payment Dashboard": {
		"on_update": "zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.PaymentDashboard.update_dashboard_stats"
	},
	"Subscription": {
		"on_submit": "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.subscription_events.on_subscription_submit",
		"on_update": "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.subscription_events.on_subscription_update",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    "all": [
        "zoyktech_zambia_payments.zoyktech_zambia_payments.utils.health_check.check_payment_gateway_health"
    ],
	"daily": [
		"zoyktech_zambia_payments.zoyktech_zambia_payments.utils.scheduled_tasks.reconcile_pending_payments",
		"zoyktech_zambia_payments.zoyktech_zambia_payments.utils.scheduled_tasks.send_payment_reports",
		"zoyktech_zambia_payments.zoyktech_zambia_payments.utils.subscription_scheduler.process_due_subscriptions",
	],
	"hourly": [
		"zoyktech_zambia_payments.zoyktech_zambia_payments.utils.scheduled_tasks.check_pending_payments",
		"zoyktech_zambia_payments.zoyktech_zambia_payments.doctype.payment_dashboard.payment_dashboard.refresh_dashboard_cache",
		"zoyktech_zambia_payments.zoyktech_zambia_payments.utils.subscription_scheduler.check_pending_subscription_payments",
	],
	"monthly": [
		"zoyktech_zambia_payments.zoyktech_zambia_payments.utils.scheduled_tasks.cleanup_old_payments"
	],
}

# Testing
# -------

before_tests = "zoyktech_zambia_payments.install.before_tests.setup_test_data"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.accounts.doctype.payment_entry.payment_entry.make_payment_entry": "zoyktech_zambia_payments.zoyktech_zambia_payments.overrides.payment_entry.make_payment_entry"
}

override_whitelisted_methods = {
	"erpnext.accounts.doctype.payment_entry.payment_entry.get_payment_entry": "zoyktech_zambia_payments.zoyktech_zambia_payments.overrides.payment_entry.get_payment_entry"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "zoyktech_zambia_payments.task.get_dashboard_data"
# }


# Fixtures
# ------------------
# Fixtures are used to automatically export and import customizations
# like Custom Fields, Property Setters, Client Scripts, etc.
fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Zoyktech Zambia Payments"]]},
	{"dt": "Property Setter"},
	{"dt": "Client Script"},
	{"dt": "Server Script"},
	{"dt": "DocType"},  # This will export your custom doctypes
]

# Website Route Rules
# ------------------------------
website_route_rules = [
	{"from_route": "/payment", "to_route": "payment"},
	{"from_route": "/payment/success", "to_route": "payment_success"},
	{"from_route": "/payment/failed", "to_route": "payment_failed"},
	{"from_route": "/payment/pending", "to_route": "payment_pending"},
]

# website_context = {
#     'favicon': '/assets/zoyktech_zambia_payments/images/favicon.ico',
#     'splash_image': '/assets/zoyktech_zambia_payments/images/logo.png'
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["zoyktech_zambia_payments.zoyktech_zambia_payments.utils.before_request"]
# after_request = ["zoyktech_zambia_payments.zoyktech_zambia_payments.utils.after_request"]

# Job Events
# ----------
# before_job = ["zoyktech_zambia_payments.zoyktech_zambia_payments.utils.before_job"]
# after_job = ["zoyktech_zambia_payments.zoyktech_zambia_payments.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"zoyktech_zambia_payments.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
	