#!/bin/bash
# Setup AWS Cost Monitoring Alerts

echo "Setting up AWS Cost Monitoring..."

# Create directories
mkdir -p aws_cost_monitoring/data
mkdir -p aws_cost_monitoring/logs
mkdir -p aws_cost_monitoring/reports

# Install dependencies
echo "Installing Python dependencies..."
pip install boto3 pandas matplotlib

# Configure AWS credentials (if not already done)
if [ ! -f ~/.aws/credentials ]; then
    echo "AWS credentials not found. Running aws configure..."
    aws configure
fi

# Create SNS topic for alerts
echo "Creating SNS topic for cost alerts..."
TOPIC_ARN=$(aws sns create-topic --name cost-alerts --region us-east-1 --query 'TopicArn' --output text)
echo "SNS Topic ARN: $TOPIC_ARN"

# Subscribe email to SNS topic
read -p "Enter email address for alerts: " EMAIL
aws sns subscribe --topic-arn $TOPIC_ARN --protocol email --notification-endpoint $EMAIL --region us-east-1
echo "Check your email and confirm the subscription!"

# Set environment variable
echo "export COST_ALERT_SNS_TOPIC=$TOPIC_ARN" >> ~/.bashrc
echo "export COST_ALERT_SNS_TOPIC=$TOPIC_ARN" >> ~/.zshrc

# Setup cron job for daily alerts
echo "Setting up daily cost check (runs at 9 AM)..."
CRON_CMD="0 9 * * * cd $(pwd) && python aws_cost_monitoring/cost_alert.py >> aws_cost_monitoring/logs/cron.log 2>&1"

# Add to crontab if not already there
(crontab -l 2>/dev/null | grep -v "cost_alert.py"; echo "$CRON_CMD") | crontab -

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Confirm SNS email subscription"
echo "2. Tag AWS resources with 'Project: SMH-Options-Trading'"
echo "3. Run: python aws_cost_monitoring/check_daily_cost.py"
echo "4. Wait for tomorrow's automated alert at 9 AM"
