# Agent System Implementation Plan
## Serverless Architecture with Strands Framework

**Date:** December 6, 2024  
**Status:** Planning Phase  
**Framework:** Strands Agents  
**Architecture:** Serverless (AWS Lambda + EventBridge)  
**Cost Target:** <$50/month

---

## Executive Summary

Building a 7-agent system for automated options trading using:
- **Strands Framework** for agent orchestration
- **AWS Lambda** for serverless compute (pay per execution)
- **EventBridge** for scheduling and event routing
- **DynamoDB** for state management
- **S3** for model storage
- **Our existing ML model** (84.21% accuracy) + parameter generator

**Key Insight:** The agent document suggests ML for parameters, but we've validated that rules-based is superior (80-90% vs 65-75%). We'll use our proven 2-stage system.

---

## Architecture Overview

### Serverless Components

```
┌─────────────────────────────────────────────────────────────┐
│                    AWS SERVERLESS STACK                      │
└─────────────────────────────────────────────────────────────┘

EventBridge (Scheduler)
    ↓
    9:00 AM Daily Trigger
    ↓
Lambda: Orchestrator Agent
    ├─→ Invokes: Recommendation Agent (Lambda)
    ├─→ Invokes: Risk Agent (Lambda)
    └─→ Stores: DynamoDB (recommendations table)
    
Lambda: Recommendation Agent
    ├─→ Fetches: Massive.com API (option chain)
    ├─→ Loads: S3 (ML model)
    ├─→ Uses: FeatureExtractor (our code)
    ├─→ Uses: ML Model (our LightGBM)
    ├─→ Uses: ParameterGenerator (our rules)
    └─→ Returns: Strategy + Parameters
    
Lambda: Risk Agent
    ├─→ Reads: DynamoDB (account state)
    ├─→ Validates: Position size, risk limits
    └─→ Returns: Approved/Rejected
    
Lambda: Tracking Agent (Hourly)
    ├─→ Reads: DynamoDB (open positions)
    ├─→ Fetches: Massive.com API (current prices)
    ├─→ Calculates: P&L
    └─→ Updates: DynamoDB (position status)
    
Lambda: Monitoring Agent (Real-time)
    ├─→ Triggered by: EventBridge (price alerts)
    ├─→ Checks: Market conditions vs thresholds
    └─→ Sends: SNS notifications
    
Lambda: Exit Agent (Hourly)
    ├─→ Reads: DynamoDB (positions)
    ├─→ Evaluates: Exit criteria (rules-based for now)
    └─→ Updates: DynamoDB (exit signals)
    
Lambda: Learning Agent (Weekly)
    ├─→ Triggered: Sunday 6 AM
    ├─→ Collects: Past week outcomes
    ├─→ Analyzes: Performance metrics
    └─→ Optional: Retrain models (future)

Storage:
├─ S3: ML models, historical data
├─ DynamoDB: Positions, recommendations, account state
└─ CloudWatch: Logs, metrics, alarms
```

---

## Cost Breakdown (Estimated)

### Monthly Costs

| Service | Usage | Cost |
|---------|-------|------|
| **Lambda** | 250 invocations/day × 30 days × 1s avg | $0.20 |
| **DynamoDB** | 10K reads/writes per day | $2.50 |
| **S3** | 100MB models + 1GB data | $0.50 |
| **EventBridge** | 300 rules/month | $1.00 |
| **SNS** | 100 notifications/month | $0.50 |
| **CloudWatch** | Logs + Metrics | $5.00 |
| **Massive.com API** | Options data | $29.00 |
| **Total** | | **~$39/month** ✅ |

**Cost Optimization:**
- Lambda free tier: 1M requests/month (we use ~7,500)
- DynamoDB free tier: 25GB storage (we use <1GB)
- S3 free tier: 5GB storage (we use <2GB)
- No EC2, no RDS, no always-on servers

---

## Agent Implementation with Strands

### 1. Orchestrator Agent

**Purpose:** Coordinate daily workflow

**Strands Implementation:**
```python
from strands import Agent, tool

class OrchestratorAgent(Agent):
    """Coordinates all other agents."""
    
    def __init__(self):
        super().__init__(
            name="orchestrator",
            instructions="""
            You coordinate the daily options trading workflow:
            1. Check market is open
            2. Invoke recommendation agent
            3. Invoke risk agent for validation
            4. Store approved recommendations
            5. Send notifications to user
            """,
            model="gpt-4o-mini"  # Cheap model for orchestration
        )
    
    @tool
    def check_market_status(self) -> dict:
        """Check if market is open."""
        # Implementation
        pass
    
    @tool
    def invoke_recommendation_agent(self) -> dict:
        """Trigger recommendation generation."""
        # Invokes Lambda
        pass
    
    @tool
    def invoke_risk_agent(self, recommendation: dict) -> dict:
        """Validate recommendation."""
        # Invokes Lambda
        pass
```

**Lambda Handler:**
```python
def lambda_handler(event, context):
    """EventBridge triggers this at 9:00 AM daily."""
    orchestrator = OrchestratorAgent()
    
    # Run workflow
    result = orchestrator.run(
        "Execute daily trading workflow"
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }
```

---

### 2. Recommendation Agent (CRITICAL - Uses Our ML Model)

**Purpose:** Generate trade recommendations

**Strands Implementation:**
```python
from strands import Agent, tool
import boto3
import joblib
from scripts.utils.feature_extractor import FeatureExtractor
from scripts.utils.parameter_generator import ParameterGenerator, RiskManager

class RecommendationAgent(Agent):
    """Generates trade recommendations using ML + Rules."""
    
    def __init__(self):
        super().__init__(
            name="recommendation",
            instructions="""
            You generate daily options trade recommendations:
            1. Fetch option chain from Massive.com
            2. Extract 84 features
            3. Use ML model to predict strategy (Stage 1)
            4. Use rules to generate parameters (Stage 2)
            5. Return complete trade specification
            
            IMPORTANT: Use the proven 2-stage system:
            - Stage 1: ML predicts strategy (84.21% accuracy)
            - Stage 2: Rules generate parameters (80-90% accuracy)
            
            DO NOT use ML for parameters - rules are better!
            """,
            model="gpt-4o-mini"
        )
        
        # Load our models from S3
        s3 = boto3.client('s3')
        self.ml_model = self._load_model_from_s3(s3, 'lightgbm_clean_model.pkl')
        self.label_encoder = self._load_model_from_s3(s3, 'label_encoder_clean.pkl')
        
        # Initialize our components
        self.feature_extractor = FeatureExtractor()
        self.parameter_generator = ParameterGenerator(
            risk_manager=RiskManager(account_size=10000, risk_per_trade=0.02)
        )
    
    @tool
    def fetch_option_chain(self, ticker: str = "SMH") -> dict:
        """Fetch current option chain from Massive.com."""
        # Use Massive.com API
        pass
    
    @tool
    def extract_features(self, option_chain: dict, price_history: dict) -> dict:
        """Extract 84 features using our FeatureExtractor."""
        features = self.feature_extractor.extract_features(
            option_chain=option_chain,
            price_history=price_history,
            current_date=datetime.now().strftime('%Y-%m-%d')
        )
        return features
    
    @tool
    def predict_strategy(self, features: dict) -> dict:
        """Stage 1: ML predicts strategy."""
        feature_df = self.feature_extractor.get_feature_dataframe(features)
        prediction = self.ml_model.predict(feature_df)[0]
        probabilities = self.ml_model.predict_proba(feature_df)[0]
        
        strategy = self.label_encoder.inverse_transform([prediction])[0]
        confidence = probabilities[prediction]
        
        return {
            'strategy': strategy,
            'confidence': float(confidence)
        }
    
    @tool
    def generate_parameters(self, strategy: str, option_chain: dict, 
                          features: dict, current_price: float) -> dict:
        """Stage 2: Rules generate parameters."""
        parameters = self.parameter_generator.generate(
            strategy=strategy,
            option_chain=option_chain,
            features=features,
            current_price=current_price
        )
        return parameters
    
    def _load_model_from_s3(self, s3, filename):
        """Load pickled model from S3."""
        obj = s3.get_object(
            Bucket='smh-options-models',
            Key=f'production/{filename}'
        )
        return joblib.loads(obj['Body'].read())
```

**Lambda Handler:**
```python
def lambda_handler(event, context):
    """Generate recommendation."""
    agent = RecommendationAgent()
    
    result = agent.run(
        "Generate today's options trade recommendation for SMH"
    )
    
    # Store in DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('recommendations')
    table.put_item(Item={
        'date': datetime.now().strftime('%Y-%m-%d'),
        'recommendation': result,
        'timestamp': datetime.now().isoformat()
    })
    
    return result
```

---

### 3. Risk Agent

**Purpose:** Validate trades against risk limits

**Strands Implementation:**
```python
class RiskAgent(Agent):
    """Validates trades against risk rules."""
    
    def __init__(self):
        super().__init__(
            name="risk",
            instructions="""
            You enforce risk management rules:
            1. Max 2% risk per trade
            2. Max 20% total portfolio risk
            3. Max 5 concurrent positions
            4. Min 55% win probability
            5. Daily loss limit: 4%
            
            REJECT any trade that violates these limits.
            """,
            model="gpt-4o-mini"
        )
    
    @tool
    def get_account_state(self) -> dict:
        """Get current account state from DynamoDB."""
        pass
    
    @tool
    def validate_position_size(self, trade: dict, account: dict) -> dict:
        """Check if position size is within limits."""
        pass
    
    @tool
    def validate_total_risk(self, trade: dict, account: dict) -> dict:
        """Check if total portfolio risk is acceptable."""
        pass
    
    @tool
    def check_daily_loss_limit(self, account: dict) -> dict:
        """Check if daily loss limit reached."""
        pass
```

---

### 4. Tracking Agent

**Purpose:** Monitor open positions and P&L

**Strands Implementation:**
```python
class TrackingAgent(Agent):
    """Tracks open positions and calculates P&L."""
    
    def __init__(self):
        super().__init__(
            name="tracking",
            instructions="""
            You monitor all open positions:
            1. Fetch current option prices
            2. Calculate unrealized P&L
            3. Update position status
            4. Track days held, DTE remaining
            """,
            model="gpt-4o-mini"
        )
    
    @tool
    def get_open_positions(self) -> list:
        """Get all open positions from DynamoDB."""
        pass
    
    @tool
    def fetch_current_prices(self, positions: list) -> dict:
        """Get current option prices from Massive.com."""
        pass
    
    @tool
    def calculate_pnl(self, position: dict, current_prices: dict) -> dict:
        """Calculate current P&L for position."""
        pass
    
    @tool
    def update_position_status(self, position_id: str, status: dict):
        """Update position in DynamoDB."""
        pass
```

**Lambda Handler (Hourly):**
```python
def lambda_handler(event, context):
    """Update all positions (runs hourly)."""
    agent = TrackingAgent()
    
    result = agent.run(
        "Update P&L for all open positions"
    )
    
    return result
```

---

### 5. Monitoring Agent

**Purpose:** Watch for market changes and send alerts

**Strands Implementation:**
```python
class MonitoringAgent(Agent):
    """Monitors market conditions and sends alerts."""
    
    def __init__(self):
        super().__init__(
            name="monitoring",
            instructions="""
            You watch for significant market events:
            1. VIX spikes (>3 points)
            2. Large price moves (>2%)
            3. Price approaching strikes
            4. Regime changes
            
            Send SNS alerts when thresholds breached.
            """,
            model="gpt-4o-mini"
        )
    
    @tool
    def check_vix_spike(self) -> dict:
        """Check if VIX spiked."""
        pass
    
    @tool
    def check_price_movement(self) -> dict:
        """Check for large price moves."""
        pass
    
    @tool
    def check_strike_proximity(self, positions: list) -> dict:
        """Check if price near any strikes."""
        pass
    
    @tool
    def send_alert(self, alert: dict):
        """Send SNS notification."""
        pass
```

---

### 6. Exit Agent

**Purpose:** Determine when to close positions

**Strands Implementation:**
```python
class ExitAgent(Agent):
    """Decides when to exit positions."""
    
    def __init__(self):
        super().__init__(
            name="exit",
            instructions="""
            You determine optimal exit timing using rules:
            1. Take profit at 50% gain
            2. Stop loss at -30%
            3. Exit at 21 DTE (for spreads)
            4. Exit if market regime changes significantly
            
            For now, use rules-based logic.
            Future: Add ML model for exit timing.
            """,
            model="gpt-4o-mini"
        )
    
    @tool
    def evaluate_exit_criteria(self, position: dict) -> dict:
        """Check if position should be exited."""
        pass
    
    @tool
    def create_exit_signal(self, position_id: str, reason: str):
        """Create exit signal in DynamoDB."""
        pass
```

---

### 7. Learning Agent

**Purpose:** Analyze performance and improve system

**Strands Implementation:**
```python
class LearningAgent(Agent):
    """Analyzes performance and suggests improvements."""
    
    def __init__(self):
        super().__init__(
            name="learning",
            instructions="""
            You analyze weekly performance:
            1. Collect all predictions and outcomes
            2. Calculate win rates by strategy
            3. Identify patterns in wins/losses
            4. Generate performance report
            
            Future: Retrain ML models based on outcomes.
            """,
            model="gpt-4o"  # Use smarter model for analysis
        )
    
    @tool
    def collect_weekly_data(self) -> dict:
        """Get past week's predictions and outcomes."""
        pass
    
    @tool
    def analyze_performance(self, data: dict) -> dict:
        """Calculate performance metrics."""
        pass
    
    @tool
    def generate_report(self, metrics: dict) -> str:
        """Create weekly performance report."""
        pass
```

**Lambda Handler (Weekly):**
```python
def lambda_handler(event, context):
    """Run weekly analysis (Sunday 6 AM)."""
    agent = LearningAgent()
    
    report = agent.run(
        "Analyze past week's trading performance and generate report"
    )
    
    # Send report via SNS
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:us-east-1:xxx:trading-reports',
        Subject='Weekly Trading Performance Report',
        Message=report
    )
    
    return report
```

---

## Infrastructure as Code (Terraform)

```hcl
# terraform/main.tf

# Lambda Functions
resource "aws_lambda_function" "orchestrator" {
  filename      = "lambda/orchestrator.zip"
  function_name = "options-orchestrator"
  role          = aws_iam_role.lambda_role.arn
  handler       = "orchestrator.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 512
  
  environment {
    variables = {
      MODELS_BUCKET = aws_s3_bucket.models.id
      POSITIONS_TABLE = aws_dynamodb_table.positions.name
    }
  }
}

resource "aws_lambda_function" "recommendation" {
  filename      = "lambda/recommendation.zip"
  function_name = "options-recommendation"
  role          = aws_iam_role.lambda_role.arn
  handler       = "recommendation.lambda_handler"
  runtime       = "python3.11"
  timeout       = 300  # 5 min for ML inference
  memory_size   = 2048  # Need memory for ML model
  
  environment {
    variables = {
      MODELS_BUCKET = aws_s3_bucket.models.id
      MASSIVE_API_KEY = var.massive_api_key
    }
  }
}

# ... similar for other agents

# EventBridge Rules
resource "aws_eventbridge_rule" "daily_trigger" {
  name                = "options-daily-trigger"
  description         = "Trigger orchestrator at 9:00 AM ET daily"
  schedule_expression = "cron(0 14 ? * MON-FRI *)"  # 9 AM ET = 2 PM UTC
}

resource "aws_eventbridge_target" "orchestrator" {
  rule      = aws_eventbridge_rule.daily_trigger.name
  target_id = "orchestrator"
  arn       = aws_lambda_function.orchestrator.arn
}

# DynamoDB Tables
resource "aws_dynamodb_table" "positions" {
  name           = "options-positions"
  billing_mode   = "PAY_PER_REQUEST"  # Serverless pricing
  hash_key       = "position_id"
  
  attribute {
    name = "position_id"
    type = "S"
  }
}

resource "aws_dynamodb_table" "recommendations" {
  name           = "options-recommendations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "date"
  
  attribute {
    name = "date"
    type = "S"
  }
}

# S3 Bucket for Models
resource "aws_s3_bucket" "models" {
  bucket = "smh-options-models"
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "options-trading-alerts"
}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up AWS account and IAM roles
- [ ] Create S3 bucket and upload ML models
- [ ] Create DynamoDB tables
- [ ] Set up EventBridge schedules
- [ ] Deploy basic Lambda functions

### Phase 2: Recommendation Agent (Week 2)
- [ ] Package our existing code (FeatureExtractor, ParameterGenerator)
- [ ] Create Lambda layer with dependencies (pandas, numpy, joblib, lightgbm)
- [ ] Implement Recommendation Agent with Strands
- [ ] Test with real Massive.com data
- [ ] Validate 2-stage system works in Lambda

### Phase 3: Risk & Tracking Agents (Week 3)
- [ ] Implement Risk Agent with validation rules
- [ ] Implement Tracking Agent for P&L monitoring
- [ ] Set up DynamoDB schemas
- [ ] Test position tracking workflow

### Phase 4: Monitoring & Exit Agents (Week 4)
- [ ] Implement Monitoring Agent with alerts
- [ ] Implement Exit Agent with rules
- [ ] Set up SNS notifications
- [ ] Test alert system

### Phase 5: Orchestration & Learning (Week 5)
- [ ] Implement Orchestrator Agent
- [ ] Implement Learning Agent
- [ ] Connect all agents via EventBridge
- [ ] End-to-end testing

### Phase 6: Production Deployment (Week 6)
- [ ] Paper trading for 2 weeks
- [ ] Monitor costs and performance
- [ ] Optimize Lambda memory/timeout
- [ ] Go live with real trades

---

## Key Decisions

### ✅ What We're Keeping from Our System

1. **ML Model (Stage 1):** Our LightGBM model with 84.21% accuracy
2. **Feature Extractor:** Our 84-feature extraction logic
3. **Parameter Generator:** Our rules-based parameter generation
4. **Risk Manager:** Our position sizing and validation
5. **Two-Stage Architecture:** ML for strategy, rules for parameters

### ✅ What We're Adding with Agents

1. **Orchestration:** Strands agents coordinate workflow
2. **Monitoring:** Real-time alerts and tracking
3. **Learning:** Weekly performance analysis
4. **Scalability:** Serverless architecture
5. **Cost Efficiency:** Pay only for executions

### ❌ What We're NOT Doing (From Agent Document)

1. **ML for Parameters:** Document suggests it, but we validated rules are better
2. **11 Strategy Heads:** We use single model + rules (simpler, works better)
3. **Complex Neural Networks:** Our LightGBM is faster and more interpretable
4. **Always-On Servers:** Using serverless instead

---

## Cost Optimization Strategies

1. **Lambda Memory:** Start with 512MB, increase only if needed
2. **DynamoDB:** Use on-demand pricing (no reserved capacity)
3. **S3:** Use Standard storage (models are small)
4. **CloudWatch:** Set log retention to 7 days
5. **EventBridge:** Combine rules where possible
6. **Massive.com:** Single API subscription ($29/month)

**Total Monthly Cost: ~$39** ✅

---

## Success Metrics

### Technical Metrics
- Lambda cold start: <3 seconds
- Recommendation generation: <30 seconds
- Daily cost: <$2
- System uptime: >99%

### Trading Metrics
- Strategy prediction accuracy: >80%
- Win rate: >60%
- Average return per trade: >3%
- Max drawdown: <10%

---

## Next Steps

1. **Install Strands Framework:**
   ```bash
   pip install strands-agents
   ```

2. **Set up AWS Account:**
   - Create IAM user with Lambda, DynamoDB, S3, EventBridge permissions
   - Configure AWS CLI

3. **Package Our Code:**
   - Create Lambda layers for dependencies
   - Upload ML models to S3
   - Test locally with SAM

4. **Deploy First Agent:**
   - Start with Recommendation Agent
   - Test with real data
   - Validate output

5. **Iterate:**
   - Add agents one by one
   - Test each integration
   - Monitor costs

---

**Status:** Ready to Start Implementation  
**Framework:** Strands Agents + AWS Serverless  
**Timeline:** 6 weeks to production  
**Cost:** <$50/month  
**Risk:** Low (paper trading first)

