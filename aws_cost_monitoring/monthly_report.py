#!/usr/bin/env python3
"""
Monthly AWS Cost Report
Generates comprehensive monthly cost summary and trends
"""

import boto3
import pandas as pd
import json
from datetime import datetime, timedelta
from decimal import Decimal
from check_daily_cost import DecimalEncoder


def get_monthly_costs(year, month):
    """
    Get AWS costs for entire month
    
    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
    
    Returns:
        dict: Daily costs for the month
    """
    ce = boto3.client('ce', region_name='us-east-1')
    
    # Calculate date range
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={
                'Start': start_str,
                'End': end_str
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
        
        daily_costs = {}
        
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            daily_costs[date] = {}
            
            total = Decimal('0')
            for group in result['Groups']:
                service = group['Keys'][0]
                amount = Decimal(group['Metrics']['UnblendedCost']['Amount'])
                
                service_name = service.replace('Amazon ', '').replace('AWS ', '')
                daily_costs[date][service_name] = amount
                total += amount
            
            daily_costs[date]['TOTAL'] = total
        
        return daily_costs
        
    except Exception as e:
        print(f"Error fetching monthly costs: {e}")
        return None


def generate_monthly_report(year, month):
    """Generate comprehensive monthly report"""
    
    print(f"Generating report for {year}-{month:02d}...")
    
    # Get monthly costs
    daily_costs = get_monthly_costs(year, month)
    
    if not daily_costs:
        print("❌ Failed to fetch monthly costs")
        return
    
    # Calculate statistics
    dates = sorted(daily_costs.keys())
    totals = [float(daily_costs[d]['TOTAL']) for d in dates]
    
    total_cost = sum(totals)
    avg_daily = total_cost / len(totals) if totals else 0
    max_daily = max(totals) if totals else 0
    min_daily = min(totals) if totals else 0
    
    # Service breakdown
    service_totals = {}
    for date in dates:
        for service, cost in daily_costs[date].items():
            if service != 'TOTAL':
                service_totals[service] = service_totals.get(service, Decimal('0')) + cost
    
    # Generate report
    report = f"\n{'=' * 60}\n"
    report += f"AWS Cost Report - {year}-{month:02d}\n"
    report += f"{'=' * 60}\n\n"
    
    report += f"📅 Period: {dates[0]} to {dates[-1]}\n"
    report += f"📊 Days: {len(dates)}\n\n"
    
    report += f"💰 TOTAL COST: ${total_cost:.2f}\n"
    report += f"📈 Average Daily: ${avg_daily:.2f}\n"
    report += f"📉 Min Daily: ${min_daily:.2f}\n"
    report += f"📈 Max Daily: ${max_daily:.2f}\n\n"
    
    # Budget status
    budget_target = 50.00
    if total_cost <= budget_target:
        status = f"✅ Within budget (${total_cost:.2f} / ${budget_target:.2f})"
    else:
        status = f"🔴 Over budget (${total_cost:.2f} / ${budget_target:.2f})"
    report += f"Status: {status}\n\n"
    
    # Service breakdown
    report += f"{'Service Breakdown':^60}\n"
    report += f"{'-' * 60}\n"
    
    sorted_services = sorted(service_totals.items(), key=lambda x: x[1], reverse=True)
    for service, cost in sorted_services:
        pct = (float(cost) / total_cost * 100) if total_cost > 0 else 0
        report += f"{service:30s} ${float(cost):>8.2f}  ({pct:>5.1f}%)\n"
    
    report += f"{'-' * 60}\n\n"
    
    # Daily trend
    report += f"{'Daily Cost Trend':^60}\n"
    report += f"{'-' * 60}\n"
    
    for date in dates[-7:]:  # Last 7 days
        cost = float(daily_costs[date]['TOTAL'])
        bar = '█' * int(cost * 20)  # Visual bar
        report += f"{date}  ${cost:>6.2f}  {bar}\n"
    
    report += f"{'=' * 60}\n"
    
    print(report)
    
    # Save report
    import os
    report_dir = 'aws_cost_monitoring/reports'
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = f'{report_dir}/monthly_report_{year}_{month:02d}.txt'
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"💾 Report saved to {report_file}")
    
    # Save JSON data
    json_file = f'{report_dir}/monthly_data_{year}_{month:02d}.json'
    with open(json_file, 'w') as f:
        json.dump(daily_costs, f, indent=2, cls=DecimalEncoder)
    
    print(f"💾 Data saved to {json_file}")
    
    # Save CSV
    csv_file = f'{report_dir}/monthly_costs_{year}_{month:02d}.csv'
    
    rows = []
    for date in dates:
        for service, cost in daily_costs[date].items():
            rows.append({
                'Date': date,
                'Service': service,
                'Cost': float(cost)
            })
    
    df = pd.DataFrame(rows)
    df.to_csv(csv_file, index=False)
    
    print(f"💾 CSV saved to {csv_file}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate monthly AWS cost report')
    parser.add_argument('--month', type=str, help='Month in YYYY-MM format (default: last month)')
    
    args = parser.parse_args()
    
    if args.month:
        year, month = map(int, args.month.split('-'))
    else:
        # Default to last month
        today = datetime.now()
        if today.month == 1:
            year = today.year - 1
            month = 12
        else:
            year = today.year
            month = today.month - 1
    
    generate_monthly_report(year, month)


if __name__ == '__main__':
    main()
