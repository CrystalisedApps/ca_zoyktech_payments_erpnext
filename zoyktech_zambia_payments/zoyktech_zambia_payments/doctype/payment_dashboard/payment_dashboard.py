import frappe
from frappe.model.document import Document
from frappe import _
import json
from datetime import datetime, timedelta

class PaymentDashboard(Document):
    def validate(self):
        self.update_dashboard_stats()
    
    def update_dashboard_stats(self):
        """Update dashboard statistics"""
        self.total_collections = self.get_total_collections()
        self.successful_payments = self.get_successful_payments_count()
        self.failed_payments = self.get_failed_payments_count()
        self.pending_payments = self.get_pending_payments_count()
    
    def get_total_collections(self):
        """Get total collections amount for last 30 days"""
        result = frappe.db.sql("""
            SELECT SUM(amount) 
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND payment_completed >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        return float(result[0][0] or 0)
    
    def get_successful_payments_count(self):
        """Get count of successful payments in last 30 days"""
        return frappe.db.count('Payment Transaction', {
            'status': 'Completed',
            'payment_completed': ['>=', datetime.now() - timedelta(days=30)]
        })
    
    def get_failed_payments_count(self):
        """Get count of failed payments in last 30 days"""
        return frappe.db.count('Payment Transaction', {
            'status': 'Failed',
            'payment_initiated': ['>=', datetime.now() - timedelta(days=30)]
        })
    
    def get_pending_payments_count(self):
        """Get count of pending payments"""
        return frappe.db.count('Payment Transaction', {
            'status': 'Pending'
        })

@frappe.whitelist()
def get_dashboard_data(days=30):
    """Get comprehensive dashboard data"""
    try:
        return {
            'total_collections': get_total_collections(days),
            'successful_payments': get_successful_payments_count(days),
            'failed_payments': get_failed_payments_count(days),
            'pending_payments': get_pending_payments_count(),
            'recent_transactions': get_recent_transactions(),
            'payment_methods_breakdown': get_payment_methods_breakdown(days),
            'daily_collections': get_daily_collections(days),
            'top_customers': get_top_customers(days)
        }
    except Exception as e:
        frappe.log_error(f"Error getting dashboard data: {str(e)}", "Dashboard")
        return {'error': str(e)}

def get_total_collections(days=30):
    """Get total collections for specified days"""
    result = frappe.db.sql("""
        SELECT SUM(amount) 
        FROM `tabPayment Transaction` 
        WHERE status = 'Completed' 
        AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
    """, (days,))
    return float(result[0][0] or 0)

def get_successful_payments_count(days=30):
    """Get count of successful payments"""
    return frappe.db.count('Payment Transaction', {
        'status': 'Completed',
        'payment_completed': ['>=', datetime.now() - timedelta(days=days)]
    })

def get_failed_payments_count(days=30):
    """Get count of failed payments"""
    return frappe.db.count('Payment Transaction', {
        'status': 'Failed',
        'payment_initiated': ['>=', datetime.now() - timedelta(days=days)]
    })

def get_pending_payments_count():
    """Get count of pending payments"""
    return frappe.db.count('Payment Transaction', {
        'status': 'Pending'
    })

def get_recent_transactions(limit=10):
    """Get recent payment transactions"""
    transactions = frappe.get_all('Payment Transaction',
        fields=['name', 'reference_id', 'amount', 'currency', 'status', 
                'payment_method', 'customer_email', 'payment_completed'],
        order_by='payment_completed DESC',
        limit=limit
    )
    return transactions

def get_payment_methods_breakdown(days=30):
    """Get breakdown of payments by method"""
    result = frappe.db.sql("""
        SELECT payment_method, COUNT(*) as count, SUM(amount) as total
        FROM `tabPayment Transaction` 
        WHERE status = 'Completed' 
        AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY payment_method
    """, (days,), as_dict=1)
    return result

def get_daily_collections(days=30):
    """Get daily collection data for chart"""
    result = frappe.db.sql("""
        SELECT DATE(payment_completed) as date, SUM(amount) as total
        FROM `tabPayment Transaction` 
        WHERE status = 'Completed' 
        AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(payment_completed)
        ORDER BY date
    """, (days,), as_dict=1)
    return result

def get_top_customers(limit=5, days=30):
    """Get top customers by payment volume"""
    result = frappe.db.sql("""
        SELECT customer_email, COUNT(*) as transaction_count, SUM(amount) as total_amount
        FROM `tabPayment Transaction` 
        WHERE status = 'Completed' 
        AND customer_email IS NOT NULL
        AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY customer_email
        ORDER BY total_amount DESC
        LIMIT %s
    """, (days, limit), as_dict=1)
    return result

@frappe.whitelist()
def export_payment_report(days=30, format_type='csv'):
    """Export payment report"""
    try:
        data = get_dashboard_data(days)
        
        if format_type == 'csv':
            # Generate CSV data
            csv_data = "Date,Amount,Currency,Status,Method,Customer\n"
            for transaction in data.get('recent_transactions', []):
                csv_data += f"{transaction.payment_completed},{transaction.amount},{transaction.currency},{transaction.status},{transaction.payment_method},{transaction.customer_email}\n"
            
            return {
                'success': True,
                'data': csv_data,
                'filename': f'payment_report_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        else:
            return {
                'success': True,
                'data': data
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }