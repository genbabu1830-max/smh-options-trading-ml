# AWS Cost Monitoring

Daily cost tracking for SMH Options Trading Agent System

## Overview

This folder contains scripts and tools to monitor AWS costs on a daily basis for the serverless agent architecture.

## Target Monthly Cost: < $50

### Cost Breakdown by Service

| Service | Expected Monthly | Daily Average | Notes |
|---------|-----------------|---------------|-------|
| Lambda (7 agents) | $15-20 | $0.50-0.67 | 250 trading days/year |
| EventBridge | $1-2 | $0.03-0.07 | Scheduled triggers |
| S3 Storage | $0.01 | $0.0003 | Model storage (403 KB) |
| S3 Requests | $0.10 | $0.003 | GET/PUT requests |
| CloudWatch Logs | $5-8 | $0.17-0.27 | Log storage & queries |
| DynamoDB | $5-10 | $0.17-0.33 | Position tracking |
| SNS | $0.50 | $0.02 | Notifications |
| **TOTAL** | **$27-41** | **$0.90-1.37** | Well under $50 target |

## Scripts

### 1. `check_daily_cost.py`
Fetches yesterday's AWS costs using Cost Explorer API

### 2. `cost_alert.py`
Sends alerts if daily costs exceed thresholds

### 3. `monthly_report.py`
Generates monthly cost summary and trends

### 4. `cost_dashboard.py`
Creates visual dashboard of costs over time

## Setup

### Prerequisites

```bash
# Install AWS SDK
pip install boto3 pandas matplotlib

# Configure AWS credentials
aws configure
```

### IAM Permissions Required

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast"
      ],
      "Resource": "*"
    }
  ]
}
```

## Usage

### Check Yesterday's Cost

```bash
python aws_cost_monitoring/check_daily_cost.py
```

Output:
```
AWS Cost Report - 2024-12-05
============================
Lambda: $0.45
EventBridge: $0.03
S3: $0.01
CloudWatch: $0.18
DynamoDB: $0.22
SNS: $0.01
----------------------------
TOTAL: $0.90
Status: ✅ Within budget ($0.90 / $1.67 daily target)
```

### Set Up Daily Alerts

```bash
# Run daily via cron
crontab -e

# Add this line (runs at 9 AM daily)
0 9 * * * cd /path/to/project && python aws_cost_monitoring/cost_alert.py
```

### Generate Monthly Report

```bash
python aws_cost_monitoring/monthly_report.py --month 2024-12
```

### View Cost Dashboard

```bash
python aws_cost_monitoring/cost_dashboard.py
```

## Alert Thresholds

| Threshold | Daily Cost | Action |
|-----------|-----------|--------|
| 🟢 Normal | < $1.50 | No action |
| 🟡 Warning | $1.50 - $2.00 | Email notification |
| 🔴 Critical | > $2.00 | Email + SMS alert |

## Cost Optimization Tips

### Lambda Optimization
- Use 512 MB memory (sweet spot for cost/performance)
- Set timeout to 30 seconds (prevent runaway costs)
- Use provisioned concurrency only if needed
- Enable Lambda Insights selectively

### S3 Optimization
- Use S3 Intelligent-Tiering for models
- Enable S3 Transfer Acceleration only if needed
- Compress models with gzip (already done)

### CloudWatch Optimization
- Set log retention to 7 days (not indefinite)
- Use log filtering to reduce ingestion
- Archive old logs to S3 Glacier

### DynamoDB Optimization
- Use on-demand pricing (pay per request)
- Enable TTL for old positions
- Use DynamoDB Streams only if needed

## Monitoring Best Practices

1. **Daily Review**: Check costs every morning
2. **Weekly Trends**: Look for unusual spikes
3. **Monthly Analysis**: Compare to previous months
4. **Budget Alerts**: Set AWS Budget alerts at $40, $45, $50
5. **Tag Resources**: Tag all resources with `Project: SMH-Options-Trading`

## Cost Anomaly Detection

The scripts automatically detect:
- Daily cost > 2x average
- Service cost > 3x normal
- Sudden spikes in Lambda invocations
- Unexpected S3 data transfer

## Historical Data

Cost data is stored in:
- `aws_cost_monitoring/data/daily_costs.csv` - Daily breakdown
- `aws_cost_monitoring/data/monthly_summary.csv` - Monthly totals
- `aws_cost_monitoring/reports/` - Generated reports

## Troubleshooting

### High Lambda Costs
- Check invocation count: `aws cloudwatch get-metric-statistics`
- Review execution duration
- Look for errors causing retries

### High S3 Costs
- Check data transfer: `aws cloudwatch get-metric-statistics`
- Review GET/PUT request counts
- Verify no unnecessary downloads

### High CloudWatch Costs
- Check log volume: `aws logs describe-log-groups`
- Review log retention settings
- Consider reducing log verbosity

## Support

For questions or issues:
1. Check AWS Cost Explorer in console
2. Review CloudWatch metrics
3. Contact AWS Support if costs are unexplained

---

**Last Updated:** December 6, 2024  
**Target:** < $50/month ($1.67/day average)  
**Status:** 🟢 On track
