from frappe.model.document import Document

class PaymentDashboard(Document):
    pass

# Re-export functions from payment_dashboard.py
from .payment_dashboard import (
    get_dashboard_data,
    export_dashboard_report,
    send_dashboard_email,
    refresh_dashboard_cache,
    check_table_structure
)