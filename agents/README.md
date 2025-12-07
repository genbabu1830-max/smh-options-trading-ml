# Strands Agents for SMH Options Trading

Intelligent agents for automated options trading using the Strands framework.

## Overview

This folder contains the agent implementations for the SMH Options Trading system. Agents use the Strands framework to orchestrate our existing ML model and rules-based parameter generation.

## Architecture

```
User/Scheduler
    ↓
Recommendation Agent (Strands)
    ├─→ fetch_market_data() - Get option chain from Massive.com
    ├─→ extract_features() - Convert to 84 features
    ├─→ predict_strategy() - ML model (Stage 1: 84.21% accuracy)
    ├─→ generate_parameters() - Rules engine (Stage 2: 80-90% accuracy)
    └─→ format_recommendation() - Format output
    ↓
Complete Trade Recommendation
```

## Agents

### 1. Recommendation Agent (`recommendation_agent.py`)

**Status:** ✅ Implemented

**Purpose:** Generate daily options trade recommendations

**Tools:**
- `fetch_market_data()` - Fetch option chain and price history
- `extract_features()` - Extract 84 aggregated features
- `predict_strategy()` - ML prediction (Stage 1)
- `generate_parameters()` - Rules-based parameters (Stage 2)
- `format_recommendation()` - Format final output

**Usage:**
```python
from agents.recommendation_agent import RecommendationAgent

# Create agent
agent = RecommendationAgent(ticker="SMH", use_s3=False)

# Generate recommendation
recommendation = agent.generate_recommendation()

# Print formatted output
print(recommendation['formatted_output'])
```

### 2. Risk Agent (Coming Soon)

**Purpose:** Validate trades against risk limits

### 3. Tracking Agent (Coming Soon)

**Purpose:** Monitor open positions and P&L

### 4. Monitoring Agent (Coming Soon)

**Purpose:** Watch for market changes and send alerts

### 5. Exit Agent (Coming Soon)

**Purpose:** Determine when to close positions

### 6. Learning Agent (Coming Soon)

**Purpose:** Analyze performance and improve system

### 7. Orchestrator Agent (Coming Soon)

**Purpose:** Coordinate all other agents

## Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# AWS CLI (for S3 model loading)
aws --version
```

### Install Dependencies

```bash
# Install Strands and dependencies
pip install -r agents/requirements.txt

# Or install individually
pip install strands-agents boto3 pandas numpy scikit-learn lightgbm
```

### Configure AWS (Optional - for S3 model loading)

```bash
aws configure
# Enter your AWS credentials
```

## Testing

### Run Test Suite

```bash
python agents/test_agent.py
```

**Expected Output:**
```
==================================================================
RECOMMENDATION AGENT TEST SUITE
==================================================================
Date: 2024-12-06 21:30:00

==================================================================
TEST 1: Agent Initialization
==================================================================
🔧 Initializing Recommendation Agent...
✅ ML Model loaded (84 features)
✅ Feature Extractor initialized
✅ Parameter Generator initialized
✅ Agent initialized successfully

==================================================================
TEST 2: Fetch Market Data
==================================================================
📊 Fetching market data for SMH on 2024-12-06...
✅ Market data fetched
   Ticker: SMH
   Date: 2024-12-06
   Current Price: $236.80

... (more tests)

==================================================================
TEST SUMMARY
==================================================================
✅ PASS: Agent Initialization
✅ PASS: Fetch Market Data
✅ PASS: Feature Extraction
✅ PASS: Strategy Prediction
✅ PASS: Parameter Generation
✅ PASS: Full Recommendation

Total: 6/6 tests passed (100%)

🎉 All tests passed!
```

### Test Individual Components

```python
from agents.recommendation_agent import RecommendationAgent

# Initialize
agent = RecommendationAgent(ticker="SMH", use_s3=False)

# Test market data fetch
market_data = agent.fetch_market_data()
print(market_data)

# Test feature extraction
features = agent.extract_features(market_data)
print(f"Extracted {len(features)} features")

# Test strategy prediction
strategy = agent.predict_strategy(features)
print(f"Predicted: {strategy['strategy']} ({strategy['confidence']:.1%})")

# Test parameter generation
parameters = agent.generate_parameters(
    strategy=strategy['strategy'],
    market_data=market_data,
    features=features
)
print(parameters)
```

## Development Mode vs Production Mode

### Development Mode (Local Models)

```python
# Uses local models from models_storage/
agent = RecommendationAgent(ticker="SMH", use_s3=False)
```

**Pros:**
- Fast (no S3 download)
- Works offline
- Good for testing

**Cons:**
- Models must be local
- Not suitable for Lambda

### Production Mode (S3 Models)

```python
# Loads models from S3 bucket
agent = RecommendationAgent(ticker="SMH", use_s3=True)
```

**Pros:**
- Works in Lambda
- Centralized model storage
- Easy model updates

**Cons:**
- Requires AWS credentials
- Cold start: ~2-3 seconds
- Warm start: <1ms (cached)

## Deployment

### Local Testing

```bash
# Run agent locally
python agents/recommendation_agent.py
```

### AWS Lambda Deployment

```bash
# Package agent + dependencies
cd agents
pip install -r requirements.txt -t package/
cp recommendation_agent.py package/
cd package && zip -r ../recommendation_agent.zip . && cd ..

# Upload to Lambda
aws lambda create-function \
  --function-name options-recommendation \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler recommendation_agent.lambda_handler \
  --zip-file fileb://recommendation_agent.zip \
  --timeout 300 \
  --memory-size 2048
```

### Lambda Handler

```python
# Add to recommendation_agent.py

def lambda_handler(event, context):
    """AWS Lambda handler"""
    import json
    
    # Parse request
    body = json.loads(event.get('body', '{}'))
    ticker = body.get('ticker', 'SMH')
    date = body.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Create agent (use S3 in Lambda)
    agent = RecommendationAgent(ticker=ticker, use_s3=True)
    
    # Generate recommendation
    recommendation = agent.generate_recommendation(date=date)
    
    return {
        'statusCode': 200,
        'body': json.dumps(recommendation, default=str)
    }
```

## Cost Estimates

### Per Recommendation

| Component | Cost |
|-----------|------|
| Lambda execution (30s @ 2GB) | $0.0001 |
| S3 GET request | $0.0000004 |
| Strands/Bedrock (Claude Haiku) | $0.005 |
| **Total** | **~$0.005** |

### Monthly Cost (21 trading days)

- Recommendations: 21 × $0.005 = **$0.105**
- Lambda: Covered by free tier
- S3: Covered by free tier
- **Total: ~$0.11/month** ✅

## Troubleshooting

### Issue: "Strands not installed"

```bash
pip install strands-agents
```

### Issue: "Model not found"

```bash
# Check models exist
ls models_storage/etfs/SMH/production/

# Should see:
# - lightgbm_clean_model.pkl
# - label_encoder_clean.pkl
# - feature_names_clean.json
```

### Issue: "AWS credentials not configured"

```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue: "Feature extraction failed"

Check that you have all required data:
- Option chain (DataFrame)
- Price history (DataFrame with at least 200 days)
- Current date

## Next Steps

1. **Integrate Massive.com API** - Replace mock data with real API calls
2. **Add Risk Agent** - Validate recommendations before execution
3. **Add Tracking Agent** - Monitor open positions
4. **Deploy to Lambda** - Set up serverless infrastructure
5. **Add Monitoring** - CloudWatch logs and metrics
6. **Paper Trading** - Test with real data, no real money
7. **Go Live** - Execute real trades

## Support

**Documentation:** See `STRANDS_AGENT_IMPLEMENTATION.md` for detailed guide

**Issues:** Use GitHub Issues for bug reports

**Questions:** Check `AGENT_SYSTEM_PLAN.md` for architecture details

---

**Status:** ✅ Recommendation Agent implemented and tested  
**Next:** Integrate Massive.com API and deploy to Lambda  
**Timeline:** Ready for testing now, production in 2 weeks
