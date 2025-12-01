import frappe
from frappe.model.document import Document
from frappe import _
import json
from datetime import datetime, timedelta
import csv
import io
import pdfkit
from frappe.utils import get_site_path
import pandas as pd

class PaymentDashboard(Document):
    pass

@frappe.whitelist()
def get_dashboard_data(days=30, currency="ZMW"):
    """Get comprehensive dashboard data with enhanced metrics"""
    try:
        # Convert days to int
        days_int = int(days)
        return {
            'summary_stats': get_summary_stats(days_int),
            'recent_transactions': get_recent_transactions(10),
            'payment_methods_breakdown': get_payment_methods_breakdown(days_int),
            'daily_collections': get_daily_collections(days_int, currency),
            'weekly_collections': get_weekly_collections(days_int, currency),
            'monthly_collections': get_monthly_collections(12, currency),
            'top_customers': get_top_customers(10, days_int),
            'status_distribution': get_status_distribution(),
            'hourly_activity': get_hourly_activity(days_int),
            'revenue_trend': get_revenue_trend(days_int),
            'platform_stats': get_platform_stats(days_int),
            'forecast_data': get_forecast_data(days_int, currency)
        }
    except Exception as e:
        frappe.log_error(f"Error getting dashboard data: {str(e)}", "Dashboard")
        return {'error': str(e)}

def get_table_columns_safe(table_name):
    """Safely get table columns with error handling"""
    try:
        return frappe.db.get_table_columns(table_name)
    except:
        return []

def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    columns = get_table_columns_safe(table_name)
    return column_name in columns if columns else False

def get_summary_stats(days=30):
    """Get summary statistics with safe column checks"""
    try:
        total_collections = get_total_collections(days)
        successful_payments = get_successful_payments_count(days)
        failed_payments = get_failed_payments_count(days)
        pending_payments = get_pending_payments_count()
        
        # Calculate additional metrics
        avg_transaction_value = get_average_transaction_value(days)
        conversion_rate = get_conversion_rate(days)
        total_transactions = successful_payments + failed_payments
        
        # Calculate YoY growth if possible
        yoy_growth = get_yoy_growth()
        
        # Calculate refunds if possible
        refund_amount = get_refund_amount(days)
        
        return {
            'total_collections': total_collections,
            'successful_payments': successful_payments,
            'failed_payments': failed_payments,
            'pending_payments': pending_payments,
            'avg_transaction_value': avg_transaction_value,
            'conversion_rate': conversion_rate,
            'total_transactions': total_transactions,
            'yoy_growth': yoy_growth,
            'refund_amount': refund_amount,
            'net_collections': total_collections - refund_amount
        }
    except Exception as e:
        frappe.log_error(f"Error in get_summary_stats: {str(e)}", "Dashboard")
        return {
            'total_collections': 0,
            'successful_payments': 0,
            'failed_payments': 0,
            'pending_payments': 0,
            'avg_transaction_value': 0,
            'conversion_rate': 0,
            'total_transactions': 0,
            'yoy_growth': 0,
            'refund_amount': 0,
            'net_collections': 0
        }

def get_total_collections(days=30):
    """Get total collections for specified days with safe column checks"""
    try:
        # Check if payment_completed column exists
        if not column_exists('tabPayment Transaction', 'payment_completed'):
            # Try creation date instead
            date_field = 'creation' if column_exists('tabPayment Transaction', 'creation') else 'modified'
            result = frappe.db.sql("""
                SELECT SUM(amount) 
                FROM `tabPayment Transaction` 
                WHERE status = 'Completed' 
                AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """.format(date_field=date_field), (days,))
        else:
            result = frappe.db.sql("""
                SELECT SUM(amount) 
                FROM `tabPayment Transaction` 
                WHERE status = 'Completed' 
                AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
        return float(result[0][0] or 0)
    except Exception as e:
        frappe.log_error(f"Error in get_total_collections: {str(e)}", "Dashboard")
        return 0

def get_successful_payments_count(days=30):
    """Get count of successful payments with safe date field"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        return frappe.db.count('Payment Transaction', {
            'status': 'Completed',
            date_field: ['>=', datetime.now() - timedelta(days=days)]
        })
    except Exception as e:
        frappe.log_error(f"Error in get_successful_payments_count: {str(e)}", "Dashboard")
        return 0

def get_failed_payments_count(days=30):
    """Get count of failed payments with safe date field"""
    try:
        date_field = 'payment_initiated' if column_exists('tabPayment Transaction', 'payment_initiated') else 'creation'
        
        return frappe.db.count('Payment Transaction', {
            'status': 'Failed',
            date_field: ['>=', datetime.now() - timedelta(days=days)]
        })
    except Exception as e:
        frappe.log_error(f"Error in get_failed_payments_count: {str(e)}", "Dashboard")
        return 0

def get_pending_payments_count():
    """Get count of pending payments"""
    try:
        return frappe.db.count('Payment Transaction', {'status': 'Pending'})
    except Exception as e:
        frappe.log_error(f"Error in get_pending_payments_count: {str(e)}", "Dashboard")
        return 0

def get_average_transaction_value(days=30):
    """Get average transaction value with safe column checks"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        result = frappe.db.sql("""
            SELECT AVG(amount) 
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """.format(date_field=date_field), (days,))
        return float(result[0][0] or 0)
    except Exception as e:
        frappe.log_error(f"Error in get_average_transaction_value: {str(e)}", "Dashboard")
        return 0

def get_conversion_rate(days=30):
    """Get payment conversion rate"""
    try:
        successful = get_successful_payments_count(days)
        failed = get_failed_payments_count(days)
        total = successful + failed
        
        if total > 0:
            return round((successful / total) * 100, 2)
        return 0
    except Exception as e:
        frappe.log_error(f"Error in get_conversion_rate: {str(e)}", "Dashboard")
        return 0

def get_yoy_growth():
    """Calculate Year-over-Year growth with safe column checks"""
    try:
        current_year = datetime.now().year
        last_year = current_year - 1
        
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        # Current year collections
        current_year_result = frappe.db.sql("""
            SELECT SUM(amount) 
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND YEAR({date_field}) = %s
        """.format(date_field=date_field), (current_year,))
        current_year_total = float(current_year_result[0][0] or 0)
        
        # Last year collections
        last_year_result = frappe.db.sql("""
            SELECT SUM(amount) 
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND YEAR({date_field}) = %s
        """.format(date_field=date_field), (last_year,))
        last_year_total = float(last_year_result[0][0] or 0)
        
        if last_year_total > 0:
            return round(((current_year_total - last_year_total) / last_year_total) * 100, 2)
        return 100 if current_year_total > 0 else 0
    except Exception as e:
        frappe.log_error(f"Error in get_yoy_growth: {str(e)}", "Dashboard")
        return 0

def get_refund_amount(days=30):
    """Get total refund amount with safe column checks"""
    try:
        # First check if Payment Refund table exists
        if not frappe.db.exists('DocType', 'Payment Refund'):
            return 0
            
        # Check for refund_date column
        if column_exists('tabPayment Refund', 'refund_date'):
            result = frappe.db.sql("""
                SELECT SUM(refund_amount) 
                FROM `tabPayment Refund` 
                WHERE status = 'Processed' 
                AND refund_date >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
        else:
            # Use creation date if refund_date doesn't exist
            result = frappe.db.sql("""
                SELECT SUM(refund_amount) 
                FROM `tabPayment Refund` 
                WHERE status = 'Processed' 
                AND creation >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
        return float(result[0][0] or 0)
    except Exception as e:
        frappe.log_error(f"Error in get_refund_amount: {str(e)}", "Dashboard")
        return 0

def get_recent_transactions(limit=20):
    """Get recent payment transactions with safe column checks"""
    try:
        # Check what columns exist
        columns = get_table_columns_safe('tabPayment Transaction')
        
        # Build fields list based on what exists
        fields = ['name', 'reference_id', 'amount', 'currency', 'status']
        
        # Add optional fields if they exist
        optional_fields = ['payment_method', 'customer_name', 'customer_email', 
                          'customer', 'party', 'payment_completed', 'creation',
                          'transaction_id', 'failure_reason', 'gateway_response', 
                          'payment_link', 'modified']
        
        for field in optional_fields:
            if field in columns:
                fields.append(field)
        
        # Determine date field for ordering
        date_field = 'payment_completed' if 'payment_completed' in columns else 'creation'
        
        transactions = frappe.get_all('Payment Transaction',
            fields=fields,
            order_by=f'{date_field} DESC' if date_field in columns else 'creation DESC',
            limit=limit
        )
        
        # Format dates and ensure all required fields exist
        for transaction in transactions:
            # Determine which date field to use
            date_value = None
            for date_field in ['payment_completed', 'creation', 'modified']:
                if date_field in transaction and transaction[date_field]:
                    date_value = transaction[date_field]
                    break
            
            if date_value:
                if isinstance(date_value, str):
                    transaction['formatted_date'] = date_value
                else:
                    transaction['formatted_date'] = date_value.strftime('%Y-%m-%d %H:%M')
            else:
                transaction['formatted_date'] = 'N/A'
            
            # Ensure customer_email exists in the response
            if 'customer_email' not in transaction:
                # Try to get customer info from any available field
                for field in ['customer_email', 'customer_name', 'customer', 'party']:
                    if field in transaction and transaction[field]:
                        transaction['customer_email'] = transaction[field]
                        break
                else:
                    transaction['customer_email'] = 'N/A'
        
        return transactions
        
    except Exception as e:
        frappe.log_error(f"Error in get_recent_transactions: {str(e)}", "Dashboard")
        return []

def get_payment_methods_breakdown(days=30):
    """Get breakdown of payments by method with safe column checks"""
    try:
        # Check if payment_method column exists
        if not column_exists('tabPayment Transaction', 'payment_method'):
            return []
            
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        result = frappe.db.sql("""
            SELECT 
                COALESCE(payment_method, 'Unknown') as method,
                COUNT(*) as count, 
                SUM(amount) as total,
                AVG(amount) as avg_amount
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY COALESCE(payment_method, 'Unknown')
            ORDER BY total DESC
        """.format(date_field=date_field), (days,), as_dict=1)
        
        # Calculate percentages
        total_amount = sum(item['total'] or 0 for item in result)
        total_count = sum(item['count'] for item in result)
        
        for item in result:
            item['amount_percentage'] = round((item['total'] / total_amount * 100), 2) if total_amount > 0 else 0
            item['count_percentage'] = round((item['count'] / total_count * 100), 2) if total_count > 0 else 0
        
        return result
    except Exception as e:
        frappe.log_error(f"Error in get_payment_methods_breakdown: {str(e)}", "Dashboard")
        return []

def get_daily_collections(days=30, currency="ZMW"):
    """Get daily collection data for chart with safe column checks"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        result = frappe.db.sql("""
            SELECT 
                DATE({date_field}) as date,
                SUM(amount) as total,
                COUNT(*) as count,
                AVG(amount) as avg_amount
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY DATE({date_field})
            ORDER BY date
        """.format(date_field=date_field), (days,), as_dict=1)
        
        # Format for chart
        labels = []
        amounts = []
        counts = []
        
        for item in result:
            if item['date']:
                labels.append(item['date'].strftime('%b %d'))
                amounts.append(float(item['total'] or 0))
                counts.append(item['count'])
        
        if not labels:
            return {
                'labels': [],
                'datasets': []
            }
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': f'Daily Collections ({currency})',
                    'data': amounts,
                    'borderColor': '#1a1a1a',
                    'backgroundColor': 'rgba(26, 26, 26, 0.05)',
                    'fill': True
                },
                {
                    'label': 'Transaction Count',
                    'data': counts,
                    'borderColor': '#666',
                    'backgroundColor': 'rgba(102, 102, 102, 0.05)',
                    'fill': True,
                    'yAxisID': 'y1'
                }
            ]
        }
    except Exception as e:
        frappe.log_error(f"Error in get_daily_collections: {str(e)}", "Dashboard")
        return {
            'labels': [],
            'datasets': []
        }

def get_weekly_collections(days=30, currency="ZMW"):
    """Get weekly collection data with safe column checks"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        result = frappe.db.sql("""
            SELECT 
                YEARWEEK({date_field}) as week,
                SUM(amount) as total,
                COUNT(*) as count
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY YEARWEEK({date_field})
            ORDER BY week
        """.format(date_field=date_field), (days,), as_dict=1)
        
        labels = []
        amounts = []
        
        for item in result:
            labels.append(f"Week {str(item['week'])[-2:]}")
            amounts.append(float(item['total'] or 0))
        
        if not labels:
            return {
                'labels': [],
                'datasets': []
            }
        
        return {
            'labels': labels,
            'datasets': [{
                'label': f'Weekly Collections ({currency})',
                'data': amounts,
                'backgroundColor': '#1a1a1a',
                'borderColor': '#1a1a1a'
            }]
        }
    except Exception as e:
        frappe.log_error(f"Error in get_weekly_collections: {str(e)}", "Dashboard")
        return {
            'labels': [],
            'datasets': []
        }

def get_monthly_collections(months=12, currency="ZMW"):
    """Get monthly collection data with safe column checks"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        result = frappe.db.sql("""
            SELECT 
                DATE_FORMAT({date_field}, '%Y-%m') as month,
                SUM(amount) as total,
                COUNT(*) as count
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s MONTH)
            GROUP BY DATE_FORMAT({date_field}, '%Y-%m')
            ORDER BY month
        """.format(date_field=date_field), (months,), as_dict=1)
        
        labels = []
        amounts = []
        
        for item in result:
            try:
                month_name = datetime.strptime(item['month'], '%Y-%m').strftime('%b %Y')
                labels.append(month_name)
                amounts.append(float(item['total'] or 0))
            except:
                continue
        
        if not labels:
            return {
                'labels': [],
                'datasets': []
            }
        
        return {
            'labels': labels,
            'datasets': [{
                'label': f'Monthly Collections ({currency})',
                'data': amounts,
                'borderColor': '#1a1a1a',
                'backgroundColor': 'rgba(26, 26, 26, 0.05)',
                'fill': True
            }]
        }
    except Exception as e:
        frappe.log_error(f"Error in get_monthly_collections: {str(e)}", "Dashboard")
        return {
            'labels': [],
            'datasets': []
        }

def get_top_customers(limit=10, days=30):
    """Get top customers by payment volume with safe column checks"""
    try:
        # Check what customer-related columns exist
        columns = get_table_columns_safe('tabPayment Transaction')
        
        # Determine which customer field to use
        customer_field = None
        possible_fields = ['customer_name', 'customer', 'customer_email', 'party', 'payer_name', 'payer_email']
        
        for field in possible_fields:
            if field in columns:
                customer_field = field
                break
        
        if not customer_field:
            # No customer field found, return empty
            return []
        
        # Determine date field
        date_field = 'payment_completed' if 'payment_completed' in columns else 'creation'
        
        query = f"""
            SELECT 
                COALESCE({customer_field}, 'Anonymous') as customer,
                COUNT(*) as transaction_count, 
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MAX({date_field}) as last_transaction
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY COALESCE({customer_field}, 'Anonymous')
            HAVING total_amount > 0
            ORDER BY total_amount DESC
            LIMIT %s
        """
        
        result = frappe.db.sql(query, (days, limit), as_dict=1)
        
        # Format last transaction date
        for customer in result:
            if customer['last_transaction']:
                if isinstance(customer['last_transaction'], str):
                    customer['last_transaction_formatted'] = customer['last_transaction']
                else:
                    customer['last_transaction_formatted'] = customer['last_transaction'].strftime('%Y-%m-%d')
            else:
                customer['last_transaction_formatted'] = 'N/A'
        
        return result
        
    except Exception as e:
        frappe.log_error(f"Error in get_top_customers: {str(e)}", "Dashboard")
        return []

def get_status_distribution():
    """Get distribution of payments by status with safe query"""
    try:
        result = frappe.db.sql("""
            SELECT 
                status,
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM `tabPayment Transaction` 
            WHERE status IN ('Completed', 'Pending', 'Failed', 'Refunded', 'Cancelled')
            GROUP BY status
            ORDER BY count DESC
        """, as_dict=1)
        
        return result
    except Exception as e:
        frappe.log_error(f"Error in get_status_distribution: {str(e)}", "Dashboard")
        return []

def get_hourly_activity(days=30):
    """Get payment activity by hour of day with safe column checks"""
    try:
        if not column_exists('tabPayment Transaction', 'payment_completed'):
            return {
                'hours': [f"{h:02d}:00" for h in range(24)],
                'counts': [0] * 24,
                'amounts': [0] * 24
            }
            
        result = frappe.db.sql("""
            SELECT 
                HOUR(payment_completed) as hour,
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY HOUR(payment_completed)
            ORDER BY hour
        """, (days,), as_dict=1)
        
        # Fill missing hours
        hours = list(range(24))
        counts = [0] * 24
        amounts = [0] * 24
        
        for item in result:
            hour = item['hour']
            counts[hour] = item['count']
            amounts[hour] = float(item['total_amount'] or 0)
        
        return {
            'hours': [f"{h:02d}:00" for h in range(24)],
            'counts': counts,
            'amounts': amounts
        }
    except Exception as e:
        frappe.log_error(f"Error in get_hourly_activity: {str(e)}", "Dashboard")
        return {
            'hours': [f"{h:02d}:00" for h in range(24)],
            'counts': [0] * 24,
            'amounts': [0] * 24
        }

def get_revenue_trend(days=30):
    """Calculate revenue trend with safe column checks"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        # Get collections for last 7 days
        recent_result = frappe.db.sql("""
            SELECT SUM(amount) as total
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        """.format(date_field=date_field))
        recent_total = float(recent_result[0][0] or 0)
        
        # Get collections for previous 7 days
        previous_result = frappe.db.sql("""
            SELECT SUM(amount) as total
            FROM `tabPayment Transaction` 
            WHERE status = 'Completed' 
            AND {date_field} >= DATE_SUB(NOW(), INTERVAL 14 DAY)
            AND {date_field} < DATE_SUB(NOW(), INTERVAL 7 DAY)
        """.format(date_field=date_field))
        previous_total = float(previous_result[0][0] or 0)
        
        if previous_total > 0:
            trend_percentage = ((recent_total - previous_total) / previous_total) * 100
            return {
                'trend': 'up' if trend_percentage > 0 else 'down',
                'percentage': round(abs(trend_percentage), 2),
                'recent_total': recent_total,
                'previous_total': previous_total
            }
        
        return {'trend': 'stable', 'percentage': 0}
    except Exception as e:
        frappe.log_error(f"Error in get_revenue_trend: {str(e)}", "Dashboard")
        return {'trend': 'stable', 'percentage': 0}

def get_platform_stats(days=30):
    """Get platform performance stats with safe column checks"""
    try:
        # Check if payment_method column exists
        if not column_exists('tabPayment Transaction', 'payment_method'):
            return {
                'method_stats': [],
                'avg_processing_time': 0,
                'total_methods': 0
            }
            
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        method_stats = frappe.db.sql("""
            SELECT 
                payment_method,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as successful,
                SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) as failed
            FROM `tabPayment Transaction` 
            WHERE {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY payment_method
        """.format(date_field=date_field), (days,), as_dict=1)
        
        # Calculate success rates
        for stat in method_stats:
            total = stat['total']
            if total > 0:
                stat['success_rate'] = round((stat['successful'] / total) * 100, 2)
            else:
                stat['success_rate'] = 0
        
        # Get average processing time if columns exist
        avg_processing_time = 0
        if (column_exists('tabPayment Transaction', 'payment_initiated') and 
            column_exists('tabPayment Transaction', 'payment_completed')):
            
            processing_time = frappe.db.sql("""
                SELECT 
                    AVG(TIMESTAMPDIFF(SECOND, payment_initiated, payment_completed)) as avg_seconds
                FROM `tabPayment Transaction` 
                WHERE status = 'Completed' 
                AND payment_initiated IS NOT NULL 
                AND payment_completed IS NOT NULL
                AND payment_completed >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            
            avg_seconds = processing_time[0][0] or 0
            avg_processing_time = round(avg_seconds / 60, 2) if avg_seconds else 0
        
        return {
            'method_stats': method_stats,
            'avg_processing_time': avg_processing_time,
            'total_methods': len(method_stats)
        }
    except Exception as e:
        frappe.log_error(f"Error in get_platform_stats: {str(e)}", "Dashboard")
        return {
            'method_stats': [],
            'avg_processing_time': 0,
            'total_methods': 0
        }

def get_forecast_data(days=30, currency="ZMW"):
    """Generate simple forecast based on historical data"""
    try:
        date_field = 'payment_completed' if column_exists('tabPayment Transaction', 'payment_completed') else 'creation'
        
        # Get daily averages
        result = frappe.db.sql("""
            SELECT 
                AVG(daily_total) as avg_daily,
                STDDEV(daily_total) as std_daily
            FROM (
                SELECT 
                    DATE({date_field}) as date,
                    SUM(amount) as daily_total
                FROM `tabPayment Transaction` 
                WHERE status = 'Completed' 
                AND {date_field} >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE({date_field})
            ) as daily_totals
        """.format(date_field=date_field), (days,))
        
        avg_daily = float(result[0][0] or 0)
        std_daily = float(result[0][1] or 0)
        
        # Simple forecast for next 7 days
        import random
        forecast_days = 7
        forecast = []
        today = datetime.now().date()
        
        for i in range(forecast_days):
            forecast_date = today + timedelta(days=i+1)
            
            # Simple forecast with some randomness
            forecast_amount = avg_daily + (random.uniform(-0.2, 0.2) * std_daily)
            forecast_amount = max(forecast_amount, 0)  # Ensure non-negative
            
            forecast.append({
                'date': forecast_date.strftime('%Y-%m-%d'),
                'amount': round(forecast_amount, 2),
                'formatted_date': forecast_date.strftime('%b %d')
            })
        
        return {
            'avg_daily': round(avg_daily, 2),
            'forecast': forecast,
            'next_7_days_total': round(sum(item['amount'] for item in forecast), 2),
            'currency': currency
        }
    except Exception as e:
        frappe.log_error(f"Error in get_forecast_data: {str(e)}", "Dashboard")
        return {
            'avg_daily': 0,
            'forecast': [],
            'next_7_days_total': 0,
            'currency': currency
        }

@frappe.whitelist()
def export_dashboard_report(days=30, report_type="summary", format_type="pdf"):
    """Export comprehensive dashboard report with PDF support"""
    try:
        # Convert days to int
        days_int = int(days)
        data = get_dashboard_data(days_int)
        
        if format_type.lower() == "pdf":
            # Generate HTML for PDF
            html_content = generate_pdf_html(data, report_type, days_int)
            
            # Configure PDF options
            options = {
                'page-size': 'A4',
                'margin-top': '15mm',
                'margin-right': '10mm',
                'margin-bottom': '15mm',
                'margin-left': '10mm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            # Generate PDF
            pdf = pdfkit.from_string(html_content, False, options=options)
            
            return {
                'success': True,
                'data': pdf,
                'filename': f'payment_dashboard_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                'mime_type': 'application/pdf'
            }
            
        elif format_type.lower() == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            if report_type == "summary":
                writer.writerow(['Payment Dashboard Summary Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Period:', f'Last {days} days'])
                writer.writerow([''])
                writer.writerow(['Metric', 'Value', 'Currency'])
                
                summary = data['summary_stats']
                writer.writerow(['Total Collections', summary['total_collections'], 'ZMW'])
                writer.writerow(['Successful Payments', summary['successful_payments'], 'Count'])
                writer.writerow(['Failed Payments', summary['failed_payments'], 'Count'])
                writer.writerow(['Pending Payments', summary['pending_payments'], 'Count'])
                writer.writerow(['Average Transaction', summary['avg_transaction_value'], 'ZMW'])
                writer.writerow(['Conversion Rate', f"{summary['conversion_rate']}%", 'Percentage'])
                writer.writerow(['YoY Growth', f"{summary['yoy_growth']}%", 'Percentage'])
                
            elif report_type == "transactions":
                writer.writerow(['Recent Transactions Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([''])
                writer.writerow(['Date', 'Reference ID', 'Amount', 'Currency', 'Status', 
                               'Method', 'Customer', 'Transaction ID'])
                for txn in data['recent_transactions']:
                    writer.writerow([
                        txn.get('formatted_date', ''),
                        txn.get('reference_id', ''),
                        txn.get('amount', 0),
                        txn.get('currency', 'ZMW'),
                        txn.get('status', ''),
                        txn.get('payment_method', ''),
                        txn.get('customer_email', ''),
                        txn.get('transaction_id', '')
                    ])
            
            elif report_type == "methods":
                writer.writerow(['Payment Methods Breakdown Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Period:', f'Last {days} days'])
                writer.writerow([''])
                writer.writerow(['Payment Method', 'Transaction Count', 'Total Amount', 
                               'Average Amount', 'Amount %', 'Count %'])
                for method in data['payment_methods_breakdown']:
                    writer.writerow([
                        method.get('method', ''),
                        method.get('count', 0),
                        method.get('total', 0),
                        method.get('avg_amount', 0),
                        f"{method.get('amount_percentage', 0)}%",
                        f"{method.get('count_percentage', 0)}%"
                    ])
            
            elif report_type == "all data":
                writer.writerow(['Complete Payment Dashboard Report'])
                writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow(['Period:', f'Last {days} days'])
                writer.writerow([''])
                
                # Summary
                writer.writerow(['SUMMARY STATISTICS'])
                summary = data['summary_stats']
                writer.writerow(['Total Collections', summary['total_collections']])
                writer.writerow(['Successful Payments', summary['successful_payments']])
                writer.writerow(['Failed Payments', summary['failed_payments']])
                writer.writerow(['Pending Payments', summary['pending_payments']])
                writer.writerow(['Average Transaction', summary['avg_transaction_value']])
                writer.writerow(['Conversion Rate', f"{summary['conversion_rate']}%"])
                writer.writerow(['YoY Growth', f"{summary['yoy_growth']}%"])
                writer.writerow([''])
                
                # Recent Transactions
                writer.writerow(['RECENT TRANSACTIONS'])
                writer.writerow(['Date', 'Reference', 'Amount', 'Status', 'Method', 'Customer'])
                for txn in data['recent_transactions'][:20]:
                    writer.writerow([
                        txn.get('formatted_date', ''),
                        txn.get('reference_id', ''),
                        txn.get('amount', 0),
                        txn.get('status', ''),
                        txn.get('payment_method', ''),
                        txn.get('customer_email', '')
                    ])
                writer.writerow([''])
                
                # Payment Methods
                writer.writerow(['PAYMENT METHODS BREAKDOWN'])
                writer.writerow(['Method', 'Count', 'Total Amount', 'Percentage'])
                for method in data['payment_methods_breakdown']:
                    writer.writerow([
                        method.get('method', ''),
                        method.get('count', 0),
                        method.get('total', 0),
                        f"{method.get('amount_percentage', 0)}%"
                    ])
            
            csv_data = output.getvalue()
            output.close()
            
            return {
                'success': True,
                'data': csv_data,
                'filename': f'payment_dashboard_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                'mime_type': 'text/csv'
            }
            
        elif format_type.lower() == "json":
            return {
                'success': True,
                'data': json.dumps(data, default=str, indent=2),
                'filename': f'payment_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                'mime_type': 'application/json'
            }
            
        elif format_type.lower() == "excel":
            # Create Excel file
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_df = pd.DataFrame([data['summary_stats']])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Transactions sheet
                transactions_df = pd.DataFrame(data['recent_transactions'])
                if not transactions_df.empty:
                    transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
                
                # Methods sheet
                methods_df = pd.DataFrame(data['payment_methods_breakdown'])
                if not methods_df.empty:
                    methods_df.to_excel(writer, sheet_name='Payment Methods', index=False)
                
                # Status distribution
                status_df = pd.DataFrame(data['status_distribution'])
                if not status_df.empty:
                    status_df.to_excel(writer, sheet_name='Status Distribution', index=False)
                
                # Top customers
                customers_df = pd.DataFrame(data['top_customers'])
                if not customers_df.empty:
                    customers_df.to_excel(writer, sheet_name='Top Customers', index=False)
            
            excel_data = output.getvalue()
            output.close()
            
            return {
                'success': True,
                'data': excel_data,
                'filename': f'payment_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }
    
    except Exception as e:
        frappe.log_error(f"Export error: {str(e)}", "Dashboard Export")
        return {
            'success': False,
            'error': str(e)
        }

def generate_pdf_html(data, report_type, days):
    """Generate HTML content for PDF report"""
    
    summary = data['summary_stats']
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Payment Dashboard Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #000; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #000; padding-bottom: 10px; }}
            .header h1 {{ color: #000; margin: 0; font-size: 24px; }}
            .header .subtitle {{ color: #666; font-size: 14px; margin-top: 5px; }}
            .summary-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 30px; }}
            .summary-card {{ background: #fff; border: 1px solid #ddd; border-radius: 3px; padding: 15px; text-align: center; }}
            .summary-card .value {{ font-size: 22px; font-weight: bold; color: #000; }}
            .summary-card .label {{ font-size: 12px; color: #666; text-transform: uppercase; margin-top: 5px; }}
            .section {{ margin-bottom: 30px; }}
            .section-title {{ background: #000; color: white; padding: 10px 15px; border-radius: 3px; font-size: 16px; font-weight: bold; margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background: #f9f9f9; padding: 10px; text-align: left; border-bottom: 2px solid #ddd; font-size: 12px; color: #000; }}
            td {{ padding: 10px; border-bottom: 1px solid #eee; font-size: 12px; }}
            .footer {{ text-align: center; margin-top: 50px; color: #666; font-size: 11px; border-top: 1px solid #eee; padding-top: 10px; }}
            .currency {{ font-family: monospace; }}
            .page-break {{ page-break-before: always; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Payment Dashboard Report</h1>
            <div class="subtitle">
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                Period: Last {days} days | 
                Report Type: {report_type.title()}
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Summary Statistics</div>
            <div class="summary-grid">
                <div class="summary-card">
                    <div class="value">ZMW {summary['total_collections']:,.2f}</div>
                    <div class="label">Total Collections</div>
                </div>
                <div class="summary-card">
                    <div class="value">{summary['successful_payments']:,}</div>
                    <div class="label">Successful Payments</div>
                </div>
                <div class="summary-card">
                    <div class="value">{summary['failed_payments']:,}</div>
                    <div class="label">Failed Payments</div>
                </div>
                <div class="summary-card">
                    <div class="value">{summary['pending_payments']:,}</div>
                    <div class="label">Pending Payments</div>
                </div>
                <div class="summary-card">
                    <div class="value">ZMW {summary['avg_transaction_value']:,.2f}</div>
                    <div class="label">Avg Transaction Value</div>
                </div>
                <div class="summary-card">
                    <div class="value">{summary['conversion_rate']}%</div>
                    <div class="label">Conversion Rate</div>
                </div>
            </div>
        </div>
    """
    
    if report_type in ["transactions", "all data"]:
        html += """
        <div class="section">
            <div class="section-title">Recent Transactions</div>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Reference</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Method</th>
                        <th>Customer</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for txn in data['recent_transactions'][:15]:
            html += f"""
                    <tr>
                        <td>{txn.get('formatted_date', 'N/A')}</td>
                        <td><small>{txn.get('reference_id', '')}</small></td>
                        <td class="currency">ZMW {txn.get('amount', 0):,.2f}</td>
                        <td>{txn.get('status', '')}</td>
                        <td>{txn.get('payment_method', '')}</td>
                        <td>{txn.get('customer_email', '')}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    if report_type in ["methods", "all data"]:
        html += """
        <div class="section">
            <div class="section-title">Payment Methods Breakdown</div>
            <table>
                <thead>
                    <tr>
                        <th>Method</th>
                        <th>Transaction Count</th>
                        <th>Total Amount</th>
                        <th>Average Amount</th>
                        <th>Amount %</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for method in data['payment_methods_breakdown']:
            html += f"""
                    <tr>
                        <td>{method.get('method', 'Unknown')}</td>
                        <td>{method.get('count', 0):,}</td>
                        <td class="currency">ZMW {method.get('total', 0):,.2f}</td>
                        <td class="currency">ZMW {method.get('avg_amount', 0):,.2f}</td>
                        <td>{method.get('amount_percentage', 0)}%</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    if report_type == "all data":
        html += """
        <div class="page-break"></div>
        <div class="section">
            <div class="section-title">Status Distribution</div>
            <table>
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Count</th>
                        <th>Total Amount</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for status in data['status_distribution']:
            html += f"""
                    <tr>
                        <td>{status.get('status', '')}</td>
                        <td>{status.get('count', 0):,}</td>
                        <td class="currency">ZMW {status.get('total_amount', 0):,.2f}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <div class="section-title">Top Customers</div>
            <table>
                <thead>
                    <tr>
                        <th>Customer</th>
                        <th>Transactions</th>
                        <th>Total Amount</th>
                        <th>Last Transaction</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for customer in data['top_customers']:
            html += f"""
                    <tr>
                        <td>{customer.get('customer', 'Anonymous')}</td>
                        <td>{customer.get('transaction_count', 0):,}</td>
                        <td class="currency">ZMW {customer.get('total_amount', 0):,.2f}</td>
                        <td>{customer.get('last_transaction_formatted', 'N/A')}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </div>
        """
    
    html += f"""
        <div class="footer">
            Report generated by Payment Dashboard System<br>
            {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Confidential Business Document
        </div>
    </body>
    </html>
    """
    
    return html

@frappe.whitelist()
def send_dashboard_email(email, days=30, report_type="summary"):
    """Send dashboard report via email"""
    try:
        # Convert days to int
        days_int = int(days)
        # Generate report
        report_data = export_dashboard_report(days_int, report_type, "pdf")
        
        if not report_data['success']:
            return report_data
        
        # Create email
        subject = f"Payment Dashboard Report - {datetime.now().strftime('%Y-%m-%d')}"
        message = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #000;">Payment Dashboard Report</h2>
            <p>Dear User,</p>
            <p>Please find attached the payment dashboard report for the last {days} days.</p>
            <div style="background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 3px; margin: 15px 0;">
                <p><strong>Report Details:</strong></p>
                <ul>
                    <li>Report Type: {report_type.capitalize()}</li>
                    <li>Period: Last {days} days</li>
                    <li>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li>Format: PDF</li>
                </ul>
            </div>
            <p>The report contains comprehensive analytics of your payment transactions.</p>
            <br>
            <p>Best regards,<br>
            <strong>Payment Dashboard System</strong></p>
        </div>
        """
        
        # Send email with attachment
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=message,
            attachments=[{
                'fname': report_data['filename'],
                'fcontent': report_data['data']
            }]
        )
        
        return {
            'success': True,
            'message': f"Report sent successfully to {email}"
        }
    
    except Exception as e:
        frappe.log_error(f"Email send error: {str(e)}", "Dashboard Email")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def refresh_dashboard_cache():
    """Force refresh dashboard cache"""
    try:
        # Clear any cached data
        frappe.cache().delete_keys('payment_dashboard_*')
        
        return {
            'success': True,
            'message': 'Dashboard cache refreshed successfully'
        }
    
    except Exception as e:
        frappe.log_error(f"Cache refresh error: {str(e)}", "Dashboard Cache")
        return {
            'success': False,
            'error': str(e)
        }

@frappe.whitelist()
def check_table_structure():
    """Debug function to check Payment Transaction table structure"""
    try:
        columns = get_table_columns_safe('tabPayment Transaction')
        
        # Check for specific columns
        important_columns = {
            'customer_name': 'customer_name' in columns,
            'customer_email': 'customer_email' in columns,
            'customer': 'customer' in columns,
            'party': 'party' in columns,
            'payment_completed': 'payment_completed' in columns,
            'payment_initiated': 'payment_initiated' in columns,
            'payment_method': 'payment_method' in columns,
            'reference_id': 'reference_id' in columns,
            'transaction_id': 'transaction_id' in columns,
            'amount': 'amount' in columns,
            'currency': 'currency' in columns,
            'status': 'status' in columns
        }
        
        # Get sample data
        sample = frappe.db.sql("SELECT * FROM `tabPayment Transaction` LIMIT 1", as_dict=True)
        
        return {
            'all_columns': columns,
            'important_columns': important_columns,
            'total_columns': len(columns),
            'sample_record': sample[0] if sample else {}
        }
    except Exception as e:
        return {
            'error': str(e),
            'all_columns': [],
            'important_columns': {},
            'total_columns': 0,
            'sample_record': {}
        }