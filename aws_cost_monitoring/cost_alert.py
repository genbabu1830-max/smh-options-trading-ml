#!/usr/bin/env python3
"""
AWS Cost Alert System
Sends alerts if daily costs exceed thresholds
"""

import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
from check_daily_cost import get_daily_cost, DecimalEncoder


# Alert thresholds (daily)
THRESHOLDS = {
    'normal': Decimal('1.50'),      # < $1.50 = OK
    'warning': Decimal('2.00'),     # $1.50-$2.00 = Warning
    'critical': Decimal('2.50')     # > $2.50 = Critical
}


def check_cost_threshold(costs):
    """
    Check if costs exceed thresholds
    
    Returns:
        tuple: (level, message)
        level: 'normal', 'warning', or 'critical'
    """
    total = costs.get('TOTAL', Decimal('0'))
    date = costs.get('date', 'Unknown')
    
    if total >= THRESHOLDS['critical']:
        level = 'critical'
        message = f"🔴 CRITICAL: AWS costs are ${float(total):.2f} on {date}"
    elif total >= THRESHOLDS['warning']:
        level = 'warning'
        message = f"🟡 WARNING: AWS costs are ${float(total):.2f} on {date}"
    else:
        level = 'normal'
        message = f"✅ NORMAL: AWS costs are ${float(total):.2f} on {date}"
    
    return level, message


def send_email_alert(subject, message, costs):
    """Send email alert via SNS"""
    try:
        sns = boto3.client('sns', region_name='us-east-1')
        
        # Format detailed message
        body = f"{message}\n\n"
        body += "Cost Breakdown:\n"
        body += "-" * 40 + "\n"
        
        services = {k: v for k, v in costs.items() if k not in ['TOTAL', 'date']}
        sorted_services = sorted(services.items(), key=lambda x: x[1], reverse=True)
        
        for service, cost in sorted_services:
            body += f"{service:20s}: ${float(cost):>6.2f}\n"
        
        body += "-" * 40 + "\n"
        body += f"{'TOTAL':20s}: ${float(costs['TOTAL']):>6.2f}\n"
        body += "\n"
        body += f"Monthly Projection: ${float(costs['TOTAL'] * 30):.2f}\n"
        body += "\n"
        body += "Check AWS Cost Explorer for details:\n"
        body += "https://console.aws.amazon.com/cost-management/home#/cost-explorer\n"
        
        # Get SNS topic ARN from environment or use default
        import os
        topic_arn = os.environ.get('COST_ALERT_SNS_TOPIC', 
                                   'arn:aws:sns:us-east-1:969748929153:cost-alerts')
        
        response = sns.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=body
        )
        
        print(f"📧 Email alert sent (MessageId: {response['MessageId']})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send email alert: {e}")
        return False


def send_slack_alert(message, costs):
    """Send alert to Slack webhook"""
    try:
        import requests
        import os
        
        webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
        if not webhook_url:
            print("⚠️  SLACK_WEBHOOK_URL not set, skipping Slack notification")
            return False
        
        # Format Slack message
        total = float(costs['TOTAL'])
        date = costs.get('date', 'Unknown')
        
        # Determine color based on level
        if total >= float(THRESHOLDS['critical']):
            color = 'danger'
            emoji = '🔴'
        elif total >= float(THRESHOLDS['warning']):
            color = 'warning'
            emoji = '🟡'
        else:
            color = 'good'
            emoji = '✅'
        
        # Build service breakdown
        services = {k: v for k, v in costs.items() if k not in ['TOTAL', 'date']}
        sorted_services = sorted(services.items(), key=lambda x: x[1], reverse=True)
        
        fields = []
        for service, cost in sorted_services[:5]:  # Top 5 services
            fields.append({
                'title': service,
                'value': f"${float(cost):.2f}",
                'short': True
            })
        
        payload = {
            'text': f"{emoji} AWS Cost Alert - {date}",
            'attachments': [
                {
                    'color': color,
                    'fields': [
                        {
                            'title': 'Total Daily Cost',
                            'value': f"${total:.2f}",
                            'short': True
                        },
                        {
                            'title': 'Monthly Projection',
                            'value': f"${total * 30:.2f}",
                            'short': True
                        }
                    ] + fields
                }
            ]
        }
        
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
        print(f"💬 Slack alert sent")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send Slack alert: {e}")
        return False


def log_alert(level, message, costs):
    """Log alert to file"""
    import os
    
    log_dir = 'aws_cost_monitoring/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = f'{log_dir}/cost_alerts.log'
    
    with open(log_file, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {level.upper()}: {message}\n")
        f.write(f"  Total: ${float(costs['TOTAL']):.2f}\n")
        f.write(f"  Details: {json.dumps(costs, cls=DecimalEncoder)}\n")
        f.write("\n")
    
    print(f"📝 Alert logged to {log_file}")


def main():
    """Main function"""
    print("Checking AWS costs for alerts...")
    
    # Get yesterday's costs
    costs = get_daily_cost()
    
    if not costs:
        print("❌ Failed to fetch cost data")
        return
    
    # Check threshold
    level, message = check_cost_threshold(costs)
    
    print(f"\n{message}")
    
    # Log all alerts
    log_alert(level, message, costs)
    
    # Send notifications based on level
    if level == 'critical':
        print("\n🚨 CRITICAL ALERT - Sending notifications...")
        send_email_alert(
            subject="🔴 CRITICAL: AWS Costs Exceeded Threshold",
            message=message,
            costs=costs
        )
        send_slack_alert(message, costs)
        
    elif level == 'warning':
        print("\n⚠️  WARNING - Sending notifications...")
        send_email_alert(
            subject="🟡 WARNING: AWS Costs Above Normal",
            message=message,
            costs=costs
        )
        send_slack_alert(message, costs)
        
    else:
        print("\n✅ Costs are within normal range")
    
    # Check for anomalies (cost > 2x average)
    try:
        import pandas as pd
        
        csv_file = 'aws_cost_monitoring/data/daily_costs.csv'
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            total_df = df[df['Service'] == 'TOTAL']
            
            if len(total_df) > 7:  # Need at least 7 days of history
                avg_cost = total_df['Cost'].tail(7).mean()
                current_cost = float(costs['TOTAL'])
                
                if current_cost > avg_cost * 2:
                    anomaly_msg = f"⚠️  ANOMALY DETECTED: Today's cost (${current_cost:.2f}) is 2x the 7-day average (${avg_cost:.2f})"
                    print(f"\n{anomaly_msg}")
                    log_alert('anomaly', anomaly_msg, costs)
                    send_email_alert(
                        subject="⚠️  AWS Cost Anomaly Detected",
                        message=anomaly_msg,
                        costs=costs
                    )
    except Exception as e:
        print(f"⚠️  Could not check for anomalies: {e}")


if __name__ == '__main__':
    main()
