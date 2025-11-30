#!/usr/bin/env python3
"""
Script to backup payment data for compliance and reporting
"""

import frappe
import json
import csv
import os
from datetime import datetime, timedelta
from frappe.utils import get_site_path

def backup_payment_data(days=30, backup_type='json'):
    """
    Backup payment data for specified number of days
    
    Args:
        days: Number of days to go back
        backup_type: Type of backup ('json', 'csv', 'both')
    """
    try:
        site_path = get_site_path()
        backup_dir = os.path.join(site_path, 'private', 'backups', 'payments')
        
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Get payment transactions
        transactions = get_payment_transactions(start_date, end_date)
        
        # Get payment links
        payment_links = get_payment_links(start_date, end_date)
        
        # Get refunds
        refunds = get_refunds(start_date, end_date)
        
        backup_data = {
            'metadata': {
                'backup_date': timestamp,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'records': {
                    'transactions': len(transactions),
                    'payment_links': len(payment_links),
                    'refunds': len(refunds)
                }
            },
            'transactions': transactions,
            'payment_links': payment_links,
            'refunds': refunds
        }
        
        if backup_type in ['json', 'both']:
            backup_json(backup_data, backup_dir, timestamp)
        
        if backup_type in ['csv', 'both']:
            backup_csv(backup_data, backup_dir, timestamp)
        
        print(f"Backup completed successfully: {timestamp}")
        return True
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        frappe.log_error(f"Payment data backup failed: {str(e)}", "Backup Script")
        return False

def get_payment_transactions(start_date, end_date):
    """Get payment transactions within date range"""
    transactions = frappe.get_all('Payment Transaction',
        filters={
            'payment_initiated': ['between', [start_date, end_date]]
        },
        fields=['*']
    )
    
    # Convert to serializable format
    for transaction in transactions:
        if 'gateway_response' in transaction and transaction['gateway_response']:
            try:
                # Try to parse JSON for better formatting
                transaction['gateway_response'] = json.loads(transaction['gateway_response'])
            except:
                # Keep as string if not valid JSON
                pass
    
    return transactions

def get_payment_links(start_date, end_date):
    """Get payment links within date range"""
    payment_links = frappe.get_all('Payment Link',
        filters={
            'creation': ['between', [start_date, end_date]]
        },
        fields=['*']
    )
    return payment_links

def get_refunds(start_date, end_date):
    """Get refunds within date range"""
    refunds = frappe.get_all('Payment Refund',
        filters={
            'creation': ['between', [start_date, end_date]]
        },
        fields=['*']
    )
    return refunds

def backup_json(backup_data, backup_dir, timestamp):
    """Create JSON backup"""
    filename = f'payment_backup_{timestamp}.json'
    filepath = os.path.join(backup_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"JSON backup created: {filepath}")

def backup_csv(backup_data, backup_dir, timestamp):
    """Create CSV backups for each data type"""
    
    # Transactions CSV
    if backup_data['transactions']:
        transactions_file = os.path.join(backup_dir, f'transactions_{timestamp}.csv')
        with open(transactions_file, 'w', newline='', encoding='utf-8') as f:
            if backup_data['transactions']:
                fieldnames = backup_data['transactions'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(backup_data['transactions'])
        print(f"Transactions CSV created: {transactions_file}")
    
    # Payment Links CSV
    if backup_data['payment_links']:
        links_file = os.path.join(backup_dir, f'payment_links_{timestamp}.csv')
        with open(links_file, 'w', newline='', encoding='utf-8') as f:
            if backup_data['payment_links']:
                fieldnames = backup_data['payment_links'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(backup_data['payment_links'])
        print(f"Payment links CSV created: {links_file}")
    
    # Refunds CSV
    if backup_data['refunds']:
        refunds_file = os.path.join(backup_dir, f'refunds_{timestamp}.csv')
        with open(refunds_file, 'w', newline='', encoding='utf-8') as f:
            if backup_data['refunds']:
                fieldnames = backup_data['refunds'][0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(backup_data['refunds'])
        print(f"Refunds CSV created: {refunds_file}")

def cleanup_old_backups(days_to_keep=30):
    """Clean up backup files older than specified days"""
    try:
        site_path = get_site_path()
        backup_dir = os.path.join(site_path, 'private', 'backups', 'payments')
        
        if not os.path.exists(backup_dir):
            return
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for filename in os.listdir(backup_dir):
            filepath = os.path.join(backup_dir, filename)
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                if file_time < cutoff_date:
                    os.remove(filepath)
                    print(f"Removed old backup: {filename}")
        
        print("Backup cleanup completed")
        
    except Exception as e:
        print(f"Backup cleanup failed: {str(e)}")

@frappe.whitelist()
def schedule_backup():
    """Schedule regular backup (to be called via scheduler)"""
    try:
        # Backup last 30 days of data
        success = backup_payment_data(days=30, backup_type='both')
        
        # Clean up backups older than 90 days
        cleanup_old_backups(days_to_keep=90)
        
        return {'success': success}
    
    except Exception as e:
        frappe.log_error(f"Scheduled backup failed: {str(e)}", "Backup Scheduler")
        return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # For command line execution
    import sys
    
    if len(sys.argv) > 1:
        days = int(sys.argv[1])
        backup_type = sys.argv[2] if len(sys.argv) > 2 else 'both'
    else:
        days = 30
        backup_type = 'both'
    
    frappe.init(site='your-site-name')
    frappe.connect()
    
    try:
        backup_payment_data(days=days, backup_type=backup_type)
    finally:
        frappe.destroy()