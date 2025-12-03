# utils/health_check.py
import frappe
from frappe.utils import now_datetime

def check_payment_gateway_health():
    """Regular health check to prevent stale locks"""
    try:
        # Check for long-running transactions on singles table
        result = frappe.db.sql("""
            SELECT COUNT(*) as locked_count 
            FROM information_schema.INNODB_LOCKS 
            WHERE lock_table LIKE '%tabSingles%' 
            AND lock_type = 'RECORD'
        """, as_dict=True)
        
        if result[0].locked_count > 5:
            frappe.log_error(
                f"High lock count detected on singles table: {result[0].locked_count}",
                "Payment Gateway Health Check"
            )
    except:
        pass