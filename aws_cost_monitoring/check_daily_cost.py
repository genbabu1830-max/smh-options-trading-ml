#!/usr/bin/env python3
"""
Check Daily AWS Costs
Fetches yesterday's AWS costs using Cost Explorer API
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def get_daily_cost(date=None):
    """
    Get AWS costs for a specific date
    
    Args:
        date: Date to check (defaults to yesterday)
    
    Returns:
        dict: Cost breakdown by service
    """
    ce = boto3.client('ce', region_name='us-east-1')
    
    # Default to yesterday
    if date is None:
        date = datetime.now() - timedelta(days=1)
    
    start_date = date.strftime('%Y-%m-%d')
    end_date = (date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ],
            Filter={
                'Tags': {
                    'Key': 'Project',
                    'Values': ['SMH-Options-Trading']
                }
            }
        )
        
        costs = {}
        total = Decimal('0')
        
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                amount = Decimal(group['Metrics']['UnblendedCost']['Amount'])
                
                # Simplify service names
                service_name = service.replace('Amazon ', '').replace('AWS ', '')
                costs[service_name] = amount
                total += amount
        
        costs['TOTAL'] = total
        costs['date'] = start_date
        
        return costs
        
    except Exception as e:
        print(f"Error fetching costs: {e}")
        return None


def format_cost_report(costs):
    """Format cost data as readable report"""
    if not costs:
        return "Unable to fetch cost data"
    
    date = costs.get('date', 'Unknown')
    total = costs.get('TOTAL', Decimal('0'))
    
    # Daily budget target ($50/month = $1.67/day)
    daily_target = Decimal('1.67')
    
    report = f"\nAWS Cost Report - {date}\n"
    report += "=" * 50 + "\n"
    
    # Sort services by cost (descending)
    services = {k: v for k, v in costs.items() if k not in ['TOTAL', 'date']}
    sorted_services = sorted(services.items(), key=lambda x: x[1], reverse=True)
    
    for service, cost in sorted_services:
        report += f"{service:20s}: ${float(cost):>6.2f}\n"
    
    report += "-" * 50 + "\n"
    report += f"{'TOTAL':20s}: ${float(total):>6.2f}\n"
    report += "=" * 50 + "\n"
    
    # Status indicator
    if total <= daily_target:
        status = f"✅ Within budget (${float(total):.2f} / ${float(daily_target):.2f} daily target)"
    elif total <= daily_target * Decimal('1.2'):
        status = f"🟡 Slightly over (${float(total):.2f} / ${float(daily_target):.2f} daily target)"
    else:
        status = f"🔴 Over budget (${float(total):.2f} / ${float(daily_target):.2f} daily target)"
    
    report += f"\nStatus: {status}\n"
    
    # Monthly projection
    monthly_projection = total * Decimal('30')
    report += f"Monthly Projection: ${float(monthly_projection):.2f}\n"
    
    return report


def save_cost_data(costs):
    """Save cost data to CSV for historical tracking"""
    import csv
    import os
    
    data_dir = 'aws_cost_monitoring/data'
    os.makedirs(data_dir, exist_ok=True)
    
    csv_file = f'{data_dir}/daily_costs.csv'
    file_exists = os.path.exists(csv_file)
    
    with open(csv_file, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Write header if new file
        if not file_exists:
            writer.writerow(['Date', 'Service', 'Cost'])
        
        # Write cost data
        date = costs.get('date', 'Unknown')
        for service, cost in costs.items():
            if service not in ['TOTAL', 'date']:
                writer.writerow([date, service, float(cost)])
        
        # Write total
        writer.writerow([date, 'TOTAL', float(costs.get('TOTAL', 0))])
    
    print(f"\n💾 Cost data saved to {csv_file}")


def main():
    """Main function"""
    print("Fetching AWS costs...")
    
    # Get yesterday's costs
    costs = get_daily_cost()
    
    if costs:
        # Print report
        print(format_cost_report(costs))
        
        # Save to CSV
        save_cost_data(costs)
        
        # Save JSON for programmatic access
        json_file = 'aws_cost_monitoring/data/latest_cost.json'
        with open(json_file, 'w') as f:
            json.dump(costs, f, indent=2, cls=DecimalEncoder)
        
        print(f"💾 Latest cost saved to {json_file}")
    else:
        print("❌ Failed to fetch cost data")
        print("\nPossible reasons:")
        print("1. AWS credentials not configured")
        print("2. Cost Explorer API not enabled")
        print("3. No resources tagged with 'Project: SMH-Options-Trading'")
        print("4. Insufficient IAM permissions")


if __name__ == '__main__':
    main()
